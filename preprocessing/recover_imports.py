"""STEP 0.2b — Import & string recovery (design section 5.3).

Strings (two complementary sources, merged):
  * FLOSS  (`floss --no static -j`): stack / tight / decoded strings found by
    FLOSS's own function emulation (no OS context needed).
  * Qiling run-time scan: run the program to completion, then read the
    image's writable segments and the heap and keep every printable string
    that does not exist statically in the file. This catches in-place
    decryptors that FLOSS misses (e.g. OLLVM `-sobf`, which decrypts global
    strings at start-up).

Imports:
  * Qiling hooks on dlopen/dlsym (Linux) or LoadLibrary/GetProcAddress
    (Windows) — see qiling_scripts/hook_imports.py.

Usage:
  python recover_imports.py <binary> [--rootfs DIR] [--os-type linux|windows]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import config
from binutil import extract_strings, load_binary
from qiling_scripts.common import new_qiling, staged_in_rootfs
from qiling_scripts.hook_imports import (recover_dynamic_imports,  # noqa: F401 (design API)
                                         recover_dynamic_imports_detailed)

MIN_LEN = 4


# =============================================================================== strings
def parse_floss_output(stdout: str) -> list:
    """Parse FLOSS JSON (-j) output into a flat, de-duplicated list."""
    try:
        doc = json.loads(stdout)
    except json.JSONDecodeError:
        # plain-text fallback: one string per line, skip FLOSS banners
        return [ln.strip() for ln in stdout.splitlines()
                if ln.strip() and not ln.startswith(("FLOSS", "+", "|", "─", "INFO"))]
    out = []
    for kind in ("decoded_strings", "stack_strings", "tight_strings"):
        for item in doc.get("strings", {}).get(kind, []):
            s = item.get("string", "")
            if s and s not in out:
                out.append(s)
    return out


def _limit_floss_memory():
    """preexec_fn: cap FLOSS's address space (config.FLOSS_MAX_MEM_GB).

    FLOSS emulates every function; on large OLLVM binaries (BinKit binutils -O0) one
    run grew to 54 GB and the kernel OOM killer took down the whole desktop session
    with it. Past the cap FLOSS fails on its own and we fall back to no FLOSS strings.
    """
    import resource
    cap = int(config.FLOSS_MAX_MEM_GB * 1024 ** 3)
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))


def recover_strings_floss(binary_path, timeout: int | None = None) -> list:
    """Run FLOSS and return its non-static strings (design API)."""
    if shutil.which(config.FLOSS_BIN) is None:
        return []
    try:
        r = subprocess.run([config.FLOSS_BIN, "--no", "static", "-j", "-q", "--", str(binary_path)],
                           capture_output=True, text=True, timeout=timeout or config.FLOSS_TIMEOUT,
                           preexec_fn=_limit_floss_memory if os.name == "posix" else None)
    except subprocess.TimeoutExpired:
        return []
    return parse_floss_output(r.stdout) if r.returncode == 0 else []


def recover_strings_dynamic(binary_path, rootfs: str, timeout_us: int | None = None) -> dict:
    """Emulate the program and harvest strings that only exist at run time."""
    timeout_us = timeout_us or config.QILING_TIMEOUT_US
    static = set(extract_strings(Path(binary_path).read_bytes(), MIN_LEN))
    with staged_in_rootfs(str(binary_path), rootfs) as staged:
        from qiling.const import QL_INTERCEPT
        ql = new_qiling(staged, rootfs)
        stdout_chunks: list = []

        def on_write(_ql, fd, buf, count, *_rest):
            if fd in (1, 2) and 0 < count < 1 << 16:
                try:
                    stdout_chunks.append(bytes(_ql.mem.read(buf, count)))
                except Exception:
                    pass

        ql.os.set_syscall("write", on_write, QL_INTERCEPT.ENTER)
        error = None
        try:
            ql.run(timeout=timeout_us)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        image_name = Path(staged).name
        from_image: list = []   # decrypted in place in .data/.bss: high confidence
        from_heap: list = []    # heap: decrypted copies, but also stdio buffers/fragments
        for start, end, perm, label, image in ql.mem.get_mapinfo():
            writable = "w" in perm if isinstance(perm, str) else bool(perm & 2)
            in_image = bool(image) and Path(image).name == image_name
            in_heap = "brk" in label or "heap" in label
            if not writable or not (in_image or in_heap) or end - start > 64 << 20:
                continue
            try:
                blob = bytes(ql.mem.read(start, end - start))
            except Exception:
                continue
            bucket = from_image if in_image else from_heap
            for s in extract_strings(blob, MIN_LEN):
                if s not in static and s not in bucket:
                    bucket.append(s)

    # heap strings that are only the tail of a longer string are leftovers of
    # reused buffers ("ecoded" from "secret message decoded") -> drop them
    every = from_image + from_heap
    heap_kept = [s for s in from_heap if s not in from_image
                 and not any(t != s and t.endswith(s) for t in every)]
    found = from_image + heap_kept
    stdout = b"".join(stdout_chunks).decode("latin-1", errors="replace")
    return {"strings": found, "stdout": stdout.splitlines(), "error": error}


def recover_strings(binary_path, rootfs: str | None = None, use_floss: bool = True,
                    use_dynamic: bool = True, details: dict | None = None) -> list:
    """Merged FLOSS + run-time strings (order: FLOSS first)."""
    details = details if details is not None else {}
    merged: list = []
    if use_floss:
        fl = recover_strings_floss(binary_path)
        details["floss"] = fl
        merged += fl
    if use_dynamic and rootfs:
        dyn = recover_strings_dynamic(binary_path, rootfs)
        details["dynamic"] = dyn["strings"]
        details["stdout"] = dyn["stdout"]
        details["dynamic_error"] = dyn["error"]
        merged += dyn["strings"]
    seen, out = set(), []
    for s in merged:
        s = s.strip("\r\n")
        if len(s) >= MIN_LEN and s not in seen:
            seen.add(s)
            out.append(s)
    return out


# =============================================================================== imports
def recover_imports(binary_path, rootfs: str, os_type: str = "linux",
                    details: dict | None = None) -> dict:
    """{"0x<addr>": "api"} for every recovered pointer slot / call site."""
    det = recover_dynamic_imports_detailed(str(binary_path), rootfs, os_type,
                                           timeout_us=config.QILING_TIMEOUT_US)
    if details is not None:
        details.update(det)
    return det["imports"]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary")
    ap.add_argument("--rootfs", default=None)
    ap.add_argument("--os-type", default=None)
    ap.add_argument("--no-floss", action="store_true")
    a = ap.parse_args()
    info = load_binary(a.binary)
    os_type = a.os_type or info.os_type
    rootfs = a.rootfs or config.default_rootfs(os_type, info.arch)
    sdet: dict = {}
    strings = recover_strings(a.binary, rootfs, use_floss=not a.no_floss, details=sdet)
    idet: dict = {}
    imports = recover_imports(a.binary, rootfs, os_type, idet)
    print(json.dumps({"strings": strings, "imports": imports,
                      "libraries": idet.get("libraries")}, indent=2))
