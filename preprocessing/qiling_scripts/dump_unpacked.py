"""Qiling-based generic unpacker: OEP detection + memory dump (design 5.2).

Idea: an unpacker writes the original code into memory and then jumps to it.
We therefore
  1. track every page of the *main image* that the emulated code writes to,
  2. watch executed basic blocks; the first block that runs from a written
     image page, entered from code that is NOT in a written image page, is
     the original entry point (OEP),
  3. stop and dump the image from emulator memory.

Dump strategies
  * ELF whose original headers were restored in memory (UPX & most ELF
    packers do this): rebuild the file from the in-memory program headers,
    so file offsets/vaddrs match the original; section headers are dropped.
  * Other ELF: synthesise a fresh ELF with one PT_LOAD per mapped region.
  * PE: classic "dump + fix headers": raw offsets := virtual offsets,
    AddressOfEntryPoint := OEP. Imports are not rebuilt (use Step 0.2b).

Usage (standalone):
  python qiling_scripts/dump_unpacked.py <packed> <rootfs> <out>
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

try:
    from .common import new_qiling, staged_in_rootfs
except ImportError:  # executed as a script
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from common import new_qiling, staged_in_rootfs

PAGE = 0x1000


def _page(a: int) -> int:
    return a & ~(PAGE - 1)


# ============================================================================ image range
def _elf_image_range(binary_path: str):
    """(lo, hi, is_dyn) of the packed file's PT_LOAD span (link-time vaddrs)."""
    import io
    from elftools.elf.elffile import ELFFile
    data = Path(binary_path).read_bytes()
    elf = ELFFile(io.BytesIO(data))
    loads = [s for s in elf.iter_segments() if s["p_type"] == "PT_LOAD"]
    lo = min(s["p_vaddr"] for s in loads)
    hi = max(s["p_vaddr"] + s["p_memsz"] for s in loads)
    return _page(lo), (hi + PAGE - 1) & ~(PAGE - 1), elf["e_type"] == "ET_DYN"


def _pe_image_range(binary_path: str):
    import pefile
    pe = pefile.PE(binary_path, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    return base, base + pe.OPTIONAL_HEADER.SizeOfImage


# ============================================================================ main entry
def find_oep_and_dump(binary_path: str, rootfs: str, output_path: str,
                      timeout_us: int = 60_000_000, verbose: bool = False) -> dict:
    """Emulate `binary_path`, detect the OEP and dump the unpacked image.

    Returns a dict: {"oep", "oep_rva", "strategy", "written_pages", "candidates"}.
    Raises RuntimeError if no OEP was found.
    """
    with staged_in_rootfs(binary_path, rootfs) as staged:
        return _find_oep_and_dump(staged, rootfs, output_path, timeout_us, verbose)


def _find_oep_and_dump(binary_path, rootfs, output_path, timeout_us, verbose) -> dict:
    data = Path(binary_path).read_bytes()
    is_pe = data[:2] == b"MZ"

    ql = new_qiling(binary_path, rootfs, verbose)

    if is_pe:
        lo, hi = _pe_image_range(binary_path)
        base_delta = ql.loader.pe_image_address - lo if hasattr(ql.loader, "pe_image_address") else 0
        lo, hi = lo + base_delta, hi + base_delta
        is_dyn = True
    else:
        lo, hi, is_dyn = _elf_image_range(binary_path)
        base_delta = ql.loader.load_address if is_dyn else 0
        lo, hi = lo + base_delta, hi + base_delta

    written: set[int] = set()
    state = {"prev_in_written": False, "oep": None, "candidates": [], "expected": None}

    def on_write(_ql, _access, addr, size, _value):
        p = _page(addr)
        written.add(p)
        end = _page(addr + size - 1)
        if end != p:
            written.add(end)

    def restored_elf_entry(_ql):
        """e_entry of an ELF header the unpacker re-wrote at the image base."""
        if is_pe or lo not in written:
            return None
        try:
            hdr = bytes(_ql.mem.read(lo, 0x40))
        except Exception:
            return None
        if hdr[:4] != b"\x7fELF":
            return None
        fmt = "<Q" if hdr[4] == 2 else "<I"
        entry = struct.unpack_from(fmt, hdr, 24)[0]
        return entry + (base_delta if is_dyn else 0)

    def on_block(_ql, addr, _size):
        in_written = lo <= addr < hi and _page(addr) in written
        if in_written and not state["prev_in_written"]:
            state["candidates"].append(addr)
            expected = restored_elf_entry(_ql)
            state["expected"] = expected
            if expected is not None and "snapshot" not in state:
                # image is already decompressed, but the dynamic loader has not
                # yet applied relocations to GOT/.dynamic -> cleanest dump
                state["snapshot"] = _read_image(_ql, lo, hi)
            # Unpacker restored the original header -> its e_entry *is* the OEP;
            # earlier candidates are helper stubs (e.g. UPX's de-filter code).
            if expected is None or expected == addr or len(state["candidates"]) > 64:
                state["oep"] = addr
                _ql.emu_stop()
        state["prev_in_written"] = in_written

    ql.hook_mem_write(on_write, begin=lo, end=hi - 1)
    ql.hook_block(on_block)
    try:
        ql.run(timeout=timeout_us)
    except Exception as exc:  # emulation crash after/before OEP
        if state["oep"] is None:
            raise RuntimeError(f"emulation failed before OEP was reached: {exc}") from exc

    oep = state["oep"]
    if oep is None and state["candidates"]:
        # program finished without hitting the restored e_entry: best effort
        oep = state["expected"] or int(state["candidates"][-1])
    if oep is None:
        raise RuntimeError("no OEP detected (no execution of freshly written image pages)")

    image = state.get("snapshot") or _read_image(ql, lo, hi)
    if is_pe:
        out, strategy = _rebuild_pe(data, image, lo, oep), "pe-fixup"
    elif image[:4] == b"\x7fELF":
        out, strategy = _rebuild_elf_from_memory(image, lo, oep, is_dyn), "elf-inmemory-headers"
    else:
        out, strategy = _synth_elf(data, ql, lo, hi, oep, is_dyn), "elf-synthesised"

    Path(output_path).write_bytes(out)
    return {
        "oep": oep,
        "oep_rva": oep - (base_delta if is_dyn else 0),
        "strategy": strategy,
        "written_pages": len(written),
        "candidates": [hex(c) for c in state["candidates"]],
        "image_range": [hex(lo), hex(hi)],
    }


# ============================================================================ memory helpers
def _read_image(ql, lo: int, hi: int) -> bytearray:
    """Read [lo, hi) page by page; unmapped pages become zeros."""
    buf = bytearray(hi - lo)
    for p in range(lo, hi, PAGE):
        try:
            buf[p - lo:p - lo + PAGE] = ql.mem.read(p, PAGE)
        except Exception:
            pass
    return buf


def _rebuild_elf_from_memory(image: bytearray, lo: int, oep: int, is_dyn: bool) -> bytes:
    """Use the ELF header + phdrs that the unpacker restored at the image base."""
    ei_class = image[4]
    is64 = ei_class == 2
    endian = "<" if image[5] == 1 else ">"
    if is64:
        (e_entry, e_phoff, e_shoff) = struct.unpack_from(endian + "QQQ", image, 24)
        e_phentsize, e_phnum = struct.unpack_from(endian + "HH", image, 54)
        ph_fmt = endian + "IIQQQQQQ"
    else:
        (e_entry, e_phoff, e_shoff) = struct.unpack_from(endian + "III", image, 24)
        e_phentsize, e_phnum = struct.unpack_from(endian + "HH", image, 42)
        ph_fmt = endian + "IIIIIIII"

    link_lo = None
    phdrs = []
    for i in range(e_phnum):
        fields = struct.unpack_from(ph_fmt, image, e_phoff + i * e_phentsize)
        if is64:
            p_type, p_flags, p_offset, p_vaddr, _pa, p_filesz, p_memsz, _al = fields
        else:
            p_type, p_offset, p_vaddr, _pa, p_filesz, p_memsz, p_flags, _al = fields
        phdrs.append((p_type, p_offset, p_vaddr, p_filesz, p_memsz))
        if p_type == 1 and (link_lo is None or p_vaddr < link_lo):
            link_lo = p_vaddr
    link_lo = _page(link_lo or 0)
    runtime_base = lo - link_lo          # 0 for ET_EXEC

    size = max((off + fsz for t, off, _va, fsz, _ms in phdrs if t == 1), default=len(image))
    out = bytearray(size)
    for p_type, p_offset, p_vaddr, p_filesz, _ in phdrs:
        if p_type != 1:
            continue
        start = p_vaddr - link_lo
        out[p_offset:p_offset + p_filesz] = image[start:start + p_filesz]

    # entry := OEP (link-time address); drop section headers (not in memory)
    new_entry = oep - runtime_base
    if is64:
        struct.pack_into(endian + "Q", out, 24, new_entry)
        struct.pack_into(endian + "Q", out, 40, 0)                 # e_shoff
        struct.pack_into(endian + "HHH", out, 58, 0, 0, 0)          # shentsize, shnum, shstrndx
    else:
        struct.pack_into(endian + "I", out, 24, new_entry)
        struct.pack_into(endian + "I", out, 32, 0)
        struct.pack_into(endian + "HHH", out, 46, 0, 0, 0)
    return bytes(out)


def _synth_elf(orig: bytes, ql, lo: int, hi: int, oep: int, is_dyn: bool) -> bytes:
    """Fresh ELF containing every mapped region of the image as a PT_LOAD."""
    is64 = orig[4] == 2
    regions = []
    for start, end, perm, _label, _img in ql.mem.get_mapinfo():
        s, e = max(start, lo), min(end, hi)
        if s < e:
            if isinstance(perm, str):     # "r-x" style
                pf = (4 if "r" in perm else 0) | (2 if "w" in perm else 0) | (1 if "x" in perm else 0)
            else:                          # UC_PROT bits: R=1 W=2 X=4
                pf = (4 if perm & 1 else 0) | (2 if perm & 2 else 0) | (1 if perm & 4 else 0)
            regions.append((s, e, pf, bytes(ql.mem.read(s, e - s))))
    base = lo if is_dyn else 0
    ehsize, phsz = (64, 56) if is64 else (52, 32)
    hdr_end = ehsize + phsz * len(regions)
    off = (hdr_end + PAGE - 1) & ~(PAGE - 1)
    body = bytearray()
    phdrs = b""
    for s, e, pf, blob in regions:
        file_off = off + len(body)
        va = s - base
        if is64:
            phdrs += struct.pack("<IIQQQQQQ", 1, pf, file_off, va, va, len(blob), len(blob), PAGE)
        else:
            phdrs += struct.pack("<IIIIIIII", 1, file_off, va, va, len(blob), len(blob), pf, PAGE)
        body += blob
    e_machine = struct.unpack_from("<H", orig, 18)[0]
    e_type = 3 if is_dyn else 2
    if is64:
        eh = orig[:16] + struct.pack("<HHIQQQIHHHHHH", e_type, e_machine, 1, oep - base, ehsize,
                                     0, 0, ehsize, phsz, len(regions), 0, 0, 0)
    else:
        eh = orig[:16] + struct.pack("<HHIIIIIHHHHHH", e_type, e_machine, 1, oep - base, ehsize,
                                     0, 0, ehsize, phsz, len(regions), 0, 0, 0)
    out = bytearray(eh + phdrs)
    out += b"\0" * (off - len(out))
    return bytes(out + body)


def _rebuild_pe(orig: bytes, image: bytearray, base: int, oep: int) -> bytes:
    import pefile
    # headers as they are in memory (the unpacker may have fixed them), else the file's
    pe = pefile.PE(data=bytes(image) if image[:2] == b"MZ" else orig, fast_load=True)
    for s in pe.sections:
        s.PointerToRawData = s.VirtualAddress
        s.SizeOfRawData = max(s.Misc_VirtualSize, s.SizeOfRawData)
    pe.OPTIONAL_HEADER.AddressOfEntryPoint = oep - base
    hdr = pe.write()[:pe.OPTIONAL_HEADER.SizeOfHeaders]
    out = bytearray(image)
    out[:len(hdr)] = hdr
    return bytes(out)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    rep = find_oep_and_dump(sys.argv[1], sys.argv[2], sys.argv[3])
    print(rep)
