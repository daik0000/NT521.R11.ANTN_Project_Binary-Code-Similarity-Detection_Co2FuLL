"""STEP 0.1 — Obfuscation signal check (design section 5.1).

Cheap static heuristics that decide whether a binary needs the full stage-0
normalisation. The goal is a low false-negative rate: flagging a clean binary
only costs some extra processing, missing an obfuscated one hurts Co2FuLL.

Signals (any one => obfuscated):
  high_entropy     file entropy > 7.0                       (packing)
  few_imports      < 5 non-CRT static imports                (packing / import hiding)
  low_strings      printable-string byte density < 0.05     (packing / string encryption)
  cff_pattern      a function compares a state value against
                   >= 6 distinct random 32-bit constants    (OLLVM control-flow flattening)
  bcf_pattern      x*(x-1)&1 / y<10 opaque predicates        (OLLVM bogus control flow)  [extra]
  packer_signature UPX!/UPX0/... markers, ELF without
                   section headers                           (packing)                  [extra]

Usage:
  python detect.py <binary> [--json]
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict

import config
from binutil import (BinaryInfo, capstone_for, load_binary, printable_string_bytes,
                     shannon_entropy)

PACKER_SECTION_NAMES = {"UPX0", "UPX1", "UPX2", ".aspack", ".adata", ".petite", ".nsp0",
                        ".nsp1", "MPRESS1", "MPRESS2", ".themida", ".vmp0", ".vmp1",
                        ".enigma1", ".enigma2"}

_COND_JUMPS = {"je", "jne", "jz", "jnz"}


# ----------------------------------------------------------------------------- metrics
def calc_file_entropy(binary_path) -> float:
    with open(binary_path, "rb") as f:
        return shannon_entropy(f.read())


def count_static_imports(binary_path, info: BinaryInfo | None = None) -> int:
    info = info or load_binary(binary_path)
    return len(info.meaningful_imports)


def calc_string_density(binary_path) -> float:
    """Fraction of file bytes that belong to printable ASCII runs of >= 4 chars."""
    with open(binary_path, "rb") as f:
        data = f.read()
    return printable_string_bytes(data) / max(len(data), 1)


def _is_state_constant(v: int) -> bool:
    """OLLVM switch-case values are uniformly random 32-bit numbers."""
    v &= 0xFFFFFFFF
    if v < 0x100000 or v > 0xFFF00000:      # small numbers / small negatives
        return False
    ones = bin(v).count("1")
    return 6 <= ones <= 26                   # excludes masks such as 0xFFFF0000


def _code_regions(info: BinaryInfo):
    """Yield (name, start_va, bytes) chunks to scan: per function if symbols exist."""
    execs = info.exec_sections()
    if info.functions:
        for name, (addr, size) in sorted(info.functions.items(), key=lambda kv: kv[1][0]):
            if size <= 0:
                continue
            code = info.read_va(addr, size)
            if code:
                yield name, addr, code
        return
    for sec in execs:
        code = info.data[sec.offset:sec.offset + sec.size]
        step = 0x1000
        for i in range(0, len(code), step):
            yield f"{sec.name}+{i:#x}", sec.vaddr + i, code[i:i + step + 64]


def scan_code_patterns(info: BinaryInfo) -> dict:
    """Disassemble code and look for CFF dispatchers and BCF opaque predicates."""
    md = capstone_for(info)
    result = {"cff_constants_max": 0, "cff_functions": {}, "bcf_predicates": 0,
              "supported": md is not None}
    if md is None:
        return result
    import capstone.x86 as x86

    for name, start, code in _code_regions(info):
        insns = list(md.disasm(code, start))
        consts = set()
        bcf = 0
        for i, ins in enumerate(insns):
            mnem = ins.mnemonic
            if mnem in ("cmp", "sub") and len(ins.operands) == 2 \
                    and ins.operands[1].type == x86.X86_OP_IMM:
                nxt = [n.mnemonic for n in insns[i + 1:i + 3]]
                if any(n in _COND_JUMPS for n in nxt) and _is_state_constant(ins.operands[1].imm):
                    consts.add(ins.operands[1].imm & 0xFFFFFFFF)
            # OLLVM BCF: (x * (x - 1)) & 1 == 0  ||  y < 10
            if mnem == "imul":
                window = insns[i + 1:i + 12]
                has_and1 = any(w.mnemonic == "and" and w.op_str.endswith(", 1") for w in window)
                has_cmp10 = any(w.mnemonic == "cmp" and w.op_str.endswith(", 0xa")
                                for w in window)
                if has_and1 and has_cmp10:
                    bcf += 1
        if len(consts) >= config.CFF_MIN_STATE_CONSTANTS:
            result["cff_functions"][name] = len(consts)
        result["cff_constants_max"] = max(result["cff_constants_max"], len(consts))
        result["bcf_predicates"] += bcf
    return result


def detect_cff_pattern(binary_path, info: BinaryInfo | None = None) -> bool:
    info = info or load_binary(binary_path)
    return bool(scan_code_patterns(info)["cff_functions"])


def detect_packer_signature(info: BinaryInfo) -> list:
    hits = []
    if b"UPX!" in info.data[:0x400] or b"UPX!" in info.data[-0x400:]:
        hits.append("UPX! magic")
    for s in info.sections:
        if s.name in PACKER_SECTION_NAMES:
            hits.append(f"section {s.name}")
    if info.fmt == "elf" and info.segments and not info.sections:
        hits.append("ELF without section headers")
    if info.fmt.endswith("-malformed"):
        hits.append("malformed headers")
    return hits


# ----------------------------------------------------------------------------- main API
def analyze_signals(binary_path) -> dict:
    """Return all metrics + boolean signals for a binary."""
    info = load_binary(binary_path)
    entropy = shannon_entropy(info.data)
    imports = info.meaningful_imports
    density = printable_string_bytes(info.data) / max(len(info.data), 1)
    patterns = scan_code_patterns(info)
    packer = detect_packer_signature(info)

    signals = {
        "high_entropy": entropy > config.ENTROPY_THRESHOLD,
        "few_imports": len(imports) < config.MIN_IMPORTS,
        "low_strings": density < config.STRING_DENSITY_THRESHOLD,
        "cff_pattern": bool(patterns["cff_functions"]),
        "bcf_pattern": patterns["bcf_predicates"] >= config.BCF_MIN_PREDICATES,
        "packer_signature": bool(packer),
    }
    return {
        "path": str(binary_path),
        "format": info.fmt,
        "arch": info.arch,
        "os_type": info.os_type,
        "is_obfuscated": any(signals.values()),
        "signals": signals,
        "metrics": {
            "entropy": round(entropy, 4),
            "import_count": len(imports),
            "imports": imports,
            "string_density": round(density, 4),
            "cff_constants_max": patterns["cff_constants_max"],
            "cff_functions": patterns["cff_functions"],
            "bcf_predicates": patterns["bcf_predicates"],
            "packer_signatures": packer,
            "code_scan_supported": patterns["supported"],
        },
    }


def check_obfuscation_signals(binary_path) -> bool:
    """True if the binary shows any obfuscation signal (design API)."""
    return analyze_signals(binary_path)["is_obfuscated"]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary", nargs="+")
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = ap.parse_args()
    rc = 0
    for b in args.binary:
        rep = analyze_signals(b)
        if args.json:
            print(json.dumps(rep, indent=2))
        else:
            fired = [k for k, v in rep["signals"].items() if v]
            tag = "OBFUSCATED" if rep["is_obfuscated"] else "CLEAN"
            m = rep["metrics"]
            print(f"[{tag}] {b}  signals={fired}  entropy={m['entropy']}  "
                  f"imports={m['import_count']}  str_density={m['string_density']}  "
                  f"cff_max={m['cff_constants_max']}  bcf={m['bcf_predicates']}")
    sys.exit(rc)
