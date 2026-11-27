"""Format-agnostic helpers for PE / ELF binaries (pyelftools + pefile)."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Imports every C program gets from the CRT; they say nothing about the
# program's behaviour, so they are not counted as "real" imports.
CRT_BOILERPLATE_IMPORTS = {
    "__libc_start_main", "__cxa_finalize", "__gmon_start__", "__stack_chk_fail",
    "_ITM_deregisterTMCloneTable", "_ITM_registerTMCloneTable", "__cxa_atexit",
    "_Jv_RegisterClasses", "__libc_csu_init", "__libc_csu_fini",
}


@dataclass
class Segment:
    vaddr: int
    memsz: int
    offset: int
    filesz: int
    perms: str  # e.g. "r-x"


@dataclass
class Section:
    name: str
    vaddr: int
    size: int
    offset: int
    executable: bool
    writable: bool
    nobits: bool = False  # .bss-like (no file content)


@dataclass
class BinaryInfo:
    path: str
    fmt: str = "unknown"          # "elf" | "pe" | "unknown"
    arch: str = "unknown"         # "x86" | "x86_64" | "arm" | "arm64" | "mips"
    bits: int = 0
    os_type: str = "unknown"      # "linux" | "windows"
    image_base: int = 0           # link-time base (PE ImageBase, ELF lowest PT_LOAD page)
    entry: int = 0
    is_pie: bool = False
    segments: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    imports: list = field(default_factory=list)      # imported function names
    functions: dict = field(default_factory=dict)    # name -> (addr, size), from symbols
    data: bytes = b""

    # ------------------------------------------------------------------ helpers
    def va_to_offset(self, va: int) -> Optional[int]:
        for s in self.segments:
            if s.vaddr <= va < s.vaddr + s.filesz:
                return s.offset + (va - s.vaddr)
        return None

    def read_va(self, va: int, size: int) -> bytes:
        off = self.va_to_offset(va)
        if off is None:
            return b""
        return self.data[off:off + size]

    def exec_sections(self) -> list:
        return [s for s in self.sections if s.executable and s.size > 0 and not s.nobits]

    def section_of(self, va: int) -> Optional[Section]:
        for s in self.sections:
            if s.vaddr <= va < s.vaddr + s.size:
                return s
        return None

    @property
    def meaningful_imports(self) -> list:
        return [i for i in self.imports if i and i not in CRT_BOILERPLATE_IMPORTS]


# =============================================================================
def detect_format(data: bytes) -> str:
    if data[:4] == b"\x7fELF":
        return "elf"
    if data[:2] == b"MZ":
        return "pe"
    return "unknown"


def load_binary(path) -> BinaryInfo:
    path = str(path)
    data = Path(path).read_bytes()
    info = BinaryInfo(path=path, data=data, fmt=detect_format(data))
    try:
        if info.fmt == "elf":
            _load_elf(info)
        elif info.fmt == "pe":
            _load_pe(info)
    except Exception as exc:  # malformed / packed headers: keep what we have
        info.fmt = info.fmt + "-malformed"
        info.__dict__.setdefault("error", str(exc))
    return info


def _load_elf(info: BinaryInfo) -> None:
    import io
    from elftools.elf.elffile import ELFFile
    from elftools.elf.sections import SymbolTableSection

    elf = ELFFile(io.BytesIO(info.data))
    machine = elf["e_machine"]
    info.arch = {
        "EM_X86_64": "x86_64", "EM_386": "x86", "EM_ARM": "arm",
        "EM_AARCH64": "arm64", "EM_MIPS": "mips",
    }.get(machine, machine)
    info.bits = elf.elfclass
    info.os_type = "linux"
    info.entry = elf["e_entry"]
    info.is_pie = elf["e_type"] == "ET_DYN"

    for seg in elf.iter_segments():
        if seg["p_type"] != "PT_LOAD":
            continue
        f = seg["p_flags"]
        perms = ("r" if f & 4 else "-") + ("w" if f & 2 else "-") + ("x" if f & 1 else "-")
        info.segments.append(Segment(seg["p_vaddr"], seg["p_memsz"], seg["p_offset"],
                                     seg["p_filesz"], perms))
    if info.segments:
        info.image_base = min(s.vaddr for s in info.segments) & ~0xFFF

    for sec in elf.iter_sections():
        if not sec.name or sec["sh_addr"] == 0:
            continue
        flags = sec["sh_flags"]
        info.sections.append(Section(
            sec.name, sec["sh_addr"], sec["sh_size"], sec["sh_offset"],
            executable=bool(flags & 0x4), writable=bool(flags & 0x1),
            nobits=sec["sh_type"] == "SHT_NOBITS"))

    imports, funcs = [], {}
    for sec in elf.iter_sections():
        if not isinstance(sec, SymbolTableSection):
            continue
        for sym in sec.iter_symbols():
            stype = sym["st_info"]["type"]
            if sec.name == ".dynsym" and sym["st_shndx"] == "SHN_UNDEF" and sym.name \
                    and stype in ("STT_FUNC", "STT_NOTYPE"):
                imports.append(sym.name.split("@")[0])
            if stype == "STT_FUNC" and sym["st_shndx"] != "SHN_UNDEF" and sym["st_value"] \
                    and sym.name:
                funcs[sym.name] = (sym["st_value"], sym["st_size"])
    # Stripped binaries keep .eh_frame, whose FDEs give the exact (start, size) of
    # every function compiled with unwind info. Without this, a stripped binary that
    # still exports a few dynamic symbols (BinKit elfedit: `error`, `warn`) exposed
    # only those functions to detect.py / cff_unflatten.py, so stage 0 found no
    # CFF/BCF signal and patched nothing.
    known = {a for a, _sz in funcs.values()}
    for start, size in _eh_frame_functions(elf, info):
        if start not in known:
            funcs[f"sub_{start:x}"] = (start, size)
    info.imports = sorted(set(imports))
    info.functions = funcs


def _eh_frame_functions(elf, info: BinaryInfo) -> list:
    """[(start, size)] of FDEs in .eh_frame that cover code outside the PLT."""
    from elftools.dwarf.callframe import FDE
    if elf.get_section_by_name(".eh_frame") is None:
        return []
    code = [s for s in info.sections if s.executable and not s.nobits and not s.name.startswith(".plt")]
    out = []
    try:
        dwarf = elf.get_dwarf_info(follow_links=False)
        if not dwarf.has_EH_CFI():
            return []
        for entry in dwarf.EH_CFI_entries():
            if not isinstance(entry, FDE):
                continue
            start, size = entry.header["initial_location"], entry.header["address_range"]
            if size > 0 and any(s.vaddr <= start < s.vaddr + s.size for s in code):
                out.append((start, size))
    except Exception:          # malformed / unusual CFI: fall back to symbols only
        return []
    return sorted(set(out))


def _load_pe(info: BinaryInfo) -> None:
    import pefile

    pe = pefile.PE(data=info.data, fast_load=True)
    pe.parse_data_directories(directories=[
        pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
        pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"],
    ])
    info.arch = {0x8664: "x86_64", 0x14C: "x86", 0x1C0: "arm", 0x1C4: "arm",
                 0xAA64: "arm64"}.get(pe.FILE_HEADER.Machine, hex(pe.FILE_HEADER.Machine))
    info.bits = 64 if info.arch in ("x86_64", "arm64") else 32
    info.os_type = "windows"
    base = pe.OPTIONAL_HEADER.ImageBase
    info.image_base = base
    info.entry = base + pe.OPTIONAL_HEADER.AddressOfEntryPoint
    info.is_pie = bool(pe.OPTIONAL_HEADER.DllCharacteristics & 0x40)
    for s in pe.sections:
        name = s.Name.rstrip(b"\0").decode("latin-1")
        ch = s.Characteristics
        va = base + s.VirtualAddress
        perms = ("r" if ch & 0x40000000 else "-") + ("w" if ch & 0x80000000 else "-") + \
                ("x" if ch & 0x20000000 else "-")
        info.segments.append(Segment(va, s.Misc_VirtualSize, s.PointerToRawData,
                                     min(s.SizeOfRawData, s.Misc_VirtualSize or s.SizeOfRawData),
                                     perms))
        info.sections.append(Section(name, va, s.Misc_VirtualSize, s.PointerToRawData,
                                     executable=bool(ch & 0x20000000),
                                     writable=bool(ch & 0x80000000),
                                     nobits=s.SizeOfRawData == 0))
    imports = []
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        for imp in entry.imports:
            if imp.name:
                imports.append(imp.name.decode("latin-1"))
            else:
                imports.append(f"ord_{imp.ordinal}")
    info.imports = sorted(set(imports))
    for exp in getattr(getattr(pe, "DIRECTORY_ENTRY_EXPORT", None), "symbols", []) or []:
        if exp.name:
            info.functions[exp.name.decode("latin-1")] = (base + exp.address, 0)


# =============================================================================
def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    n = len(data)
    return -sum(c / n * math.log2(c / n) for c in Counter(data).values())


def extract_strings(data: bytes, min_len: int = 4) -> list:
    """ASCII + UTF-16LE printable strings (like `strings -a`)."""
    out = [m.group().decode("ascii") for m in re.finditer(rb"[\x20-\x7e\t]{%d,}" % min_len, data)]
    for m in re.finditer(rb"(?:[\x20-\x7e]\x00){%d,}" % min_len, data):
        out.append(m.group().decode("utf-16le"))
    return out


def printable_string_bytes(data: bytes, min_len: int = 4) -> int:
    return sum(len(m.group()) for m in re.finditer(rb"[\x20-\x7e\t]{%d,}" % min_len, data))


def capstone_for(info: BinaryInfo):
    """Return a configured capstone Cs object (detail on) or None."""
    import capstone as cs
    if info.arch == "x86_64":
        md = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_64)
    elif info.arch == "x86":
        md = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_32)
    else:
        return None
    md.detail = True
    md.skipdata = True
    return md
