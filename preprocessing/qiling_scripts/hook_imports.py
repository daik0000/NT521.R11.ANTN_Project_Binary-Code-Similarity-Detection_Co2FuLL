"""Qiling: recover dynamically resolved imports (design 5.3 part B).

Hooks the run-time API resolvers
    Linux   : dlopen / dlsym
    Windows : LoadLibraryA/W, GetProcAddress
and follows each resolved function pointer:
  * slot      — where the program stores the pointer (its private "IAT" entry),
                found by watching memory writes of the resolved value into the image;
  * call site — every place that calls through the pointer, found by hooking
                the resolved address and reading the return address.

All addresses are reported as *link-time* virtual addresses (PIE load base
removed) so they match what Ghidra/IDA show for the binary.

Usage (standalone):
  python qiling_scripts/hook_imports.py <binary> <rootfs>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from .common import new_qiling, staged_in_rootfs
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from common import new_qiling, staged_in_rootfs


def _read_cstr(ql, ptr: int, wide: bool = False, limit: int = 512) -> str:
    if not ptr:
        return ""
    out = bytearray()
    step = 2 if wide else 1
    for i in range(0, limit * step, step):
        ch = bytes(ql.mem.read(ptr + i, step))
        if ch == b"\0" * step:
            break
        out += ch
    return out.decode("utf-16le" if wide else "latin-1", errors="replace")


def _call_site_from_return(ql, ret: int) -> int:
    """Best effort: address of the `call` instruction that returns to `ret`."""
    try:
        import capstone as cs
        mode = cs.CS_MODE_64 if ql.arch.bits == 64 else cs.CS_MODE_32
        md = cs.Cs(cs.CS_ARCH_X86, mode)
        for n in (2, 3, 5, 6, 7, 4):
            code = bytes(ql.mem.read(ret - n, n))
            insns = list(md.disasm(code, ret - n))
            if len(insns) == 1 and insns[0].mnemonic == "call" and insns[0].size == n:
                return ret - n
    except Exception:
        pass
    return ret


def recover_dynamic_imports_detailed(binary_path: str, rootfs: str, os_type: str = "linux",
                                     timeout_us: int = 60_000_000, verbose: bool = False) -> dict:
    with staged_in_rootfs(binary_path, rootfs) as staged:
        return _recover(staged, rootfs, os_type, timeout_us, verbose)


def _recover(binary_path, rootfs, os_type, timeout_us, verbose) -> dict:
    from qiling.const import QL_INTERCEPT

    ql = new_qiling(binary_path, rootfs, verbose)
    head = Path(binary_path).read_bytes()[:18]
    is_dyn = head[:4] == b"\x7fELF" and head[16] == 3          # e_type == ET_DYN (PIE)
    base = ql.loader.load_address if is_dyn else 0
    if os_type == "windows":
        base = 0  # PE is mapped at its preferred ImageBase by Qiling

    # image range (to keep only writes/calls that originate from the program)
    img_lo, img_hi = None, None
    for start, end, _perm, _label, image in ql.mem.get_mapinfo():
        if image and Path(image).name == Path(binary_path).name:
            img_lo = start if img_lo is None else min(img_lo, start)
            img_hi = end if img_hi is None else max(img_hi, end)

    def in_image(a: int) -> bool:
        return img_lo is not None and img_lo <= a < img_hi

    def link(a: int) -> int:
        return a - base if in_image(a) else a

    records: dict[int, dict] = {}       # resolved value -> record
    libraries: dict[int, str] = {}      # handle -> library name
    pending: list = []                  # stack of (api, lib, call_site) awaiting EXIT
    hooked_values: set[int] = set()

    def on_api_called(_ql, *_args):
        pc = _ql.arch.regs.arch_pc
        rec = records.get(pc)
        if rec is None:
            return
        sp = _ql.arch.regs.arch_sp
        ret = _ql.unpack(_ql.mem.read(sp, _ql.arch.pointersize))
        if in_image(ret):
            site = link(_call_site_from_return(_ql, ret))
            if site not in rec["call_sites"]:
                rec["call_sites"].append(site)

    def on_value_write(_ql, _access, addr, size, value):
        if size == _ql.arch.pointersize and value in records and in_image(addr):
            slot = link(addr)
            if slot not in records[value]["slots"]:
                records[value]["slots"].append(slot)

    def remember(value: int, api: str, lib: str, caller: int):
        if not value:
            return
        rec = records.setdefault(value, {"api": api, "library": lib, "resolver_call_site": caller,
                                         "resolved_value": value, "slots": [], "call_sites": []})
        rec["api"] = api
        if value not in hooked_values:
            hooked_values.add(value)
            ql.hook_address(on_api_called, value)

    # ------------------------------------------------------------- Linux hooks
    def dlopen_enter(_ql, *_):
        name = _read_cstr(_ql, _ql.arch.regs.rdi if _ql.arch.bits == 64 else
                          _ql.unpack32(_ql.mem.read(_ql.arch.regs.esp + 4, 4)))
        pending.append(("dlopen", name, None))

    def dlopen_exit(_ql, *_):
        if pending and pending[-1][0] == "dlopen":
            _, name, _c = pending.pop()
            libraries[_ql.arch.regs.rax if _ql.arch.bits == 64 else _ql.arch.regs.eax] = name

    def dlsym_enter(_ql, *_):
        if _ql.arch.bits == 64:
            handle, name_ptr = _ql.arch.regs.rdi, _ql.arch.regs.rsi
        else:
            sp = _ql.arch.regs.esp
            handle = _ql.unpack32(_ql.mem.read(sp + 4, 4))
            name_ptr = _ql.unpack32(_ql.mem.read(sp + 8, 4))
        ret = _ql.unpack(_ql.mem.read(_ql.arch.regs.arch_sp, _ql.arch.pointersize))
        pending.append(("dlsym", _read_cstr(_ql, name_ptr), libraries.get(handle, ""),
                        link(_call_site_from_return(_ql, ret))))

    def dlsym_exit(_ql, *_):
        if pending and pending[-1][0] == "dlsym":
            _, api, lib, caller = pending.pop()
            remember(_ql.arch.regs.rax if _ql.arch.bits == 64 else _ql.arch.regs.eax,
                     api, lib, caller)

    # ----------------------------------------------------------- Windows hooks
    def loadlib_enter(wide):
        def _cb(_ql, address, params):
            name = params.get("lpLibFileName") or params.get("lpFileName")
            if isinstance(name, int):
                name = _read_cstr(_ql, name, wide)
            pending.append(("dlopen", str(name), None))
        return _cb

    def loadlib_exit(_ql, address, params, retval):
        if pending and pending[-1][0] == "dlopen":
            libraries[retval] = pending.pop()[1]

    def gpa_enter(_ql, address, params):
        h, proc = params.get("hModule"), params.get("lpProcName")
        if isinstance(proc, int):
            proc = f"ord_{proc}" if proc < 0x10000 else _read_cstr(_ql, proc)
        ret = _ql.unpack(_ql.mem.read(_ql.arch.regs.arch_sp, _ql.arch.pointersize))
        pending.append(("dlsym", str(proc), libraries.get(h, ""), link(ret)))

    def gpa_exit(_ql, address, params, retval):
        if pending and pending[-1][0] == "dlsym":
            _, api, lib, caller = pending.pop()
            remember(retval, api, lib, caller)

    if os_type == "windows":
        ql.os.set_api("LoadLibraryA", loadlib_enter(False), QL_INTERCEPT.ENTER)
        ql.os.set_api("LoadLibraryW", loadlib_enter(True), QL_INTERCEPT.ENTER)
        ql.os.set_api("LoadLibraryA", loadlib_exit, QL_INTERCEPT.EXIT)
        ql.os.set_api("LoadLibraryW", loadlib_exit, QL_INTERCEPT.EXIT)
        ql.os.set_api("GetProcAddress", gpa_enter, QL_INTERCEPT.ENTER)
        ql.os.set_api("GetProcAddress", gpa_exit, QL_INTERCEPT.EXIT)
    else:
        ql.os.set_api("dlopen", dlopen_enter, QL_INTERCEPT.ENTER)
        ql.os.set_api("dlopen", dlopen_exit, QL_INTERCEPT.EXIT)
        ql.os.set_api("dlsym", dlsym_enter, QL_INTERCEPT.ENTER)
        ql.os.set_api("dlsym", dlsym_exit, QL_INTERCEPT.EXIT)

    if img_lo is not None:
        ql.hook_mem_write(on_value_write, begin=img_lo, end=img_hi - 1)

    error = None
    try:
        ql.run(timeout=timeout_us)
    except Exception as exc:          # keep whatever was recovered so far
        error = f"{type(exc).__name__}: {exc}"

    imports: dict[str, str] = {}
    for rec in records.values():
        for a in rec["slots"] + rec["call_sites"]:
            imports[f"{a:#x}"] = rec["api"]
    return {
        "imports": imports,
        "records": [{**r, "resolved_value": hex(r["resolved_value"]),
                     "resolver_call_site": hex(r["resolver_call_site"]) if r["resolver_call_site"] else None,
                     "slots": [hex(s) for s in r["slots"]],
                     "call_sites": [hex(c) for c in r["call_sites"]]} for r in records.values()],
        "libraries": sorted(set(libraries.values())),
        "load_base": hex(base),
        "error": error,
    }


def recover_dynamic_imports(binary_path, rootfs, os_type="linux") -> dict:
    """Design API: {"0x<addr>": "api_name"} — addr is a pointer slot or call site."""
    return recover_dynamic_imports_detailed(binary_path, rootfs, os_type)["imports"]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    rep = recover_dynamic_imports_detailed(sys.argv[1], sys.argv[2],
                                           sys.argv[3] if len(sys.argv) > 3 else "linux")
    print(json.dumps(rep, indent=2))
