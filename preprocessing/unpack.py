"""STEP 0.2a — Packing recovery (design section 5.2).

Strategy
  1. UPX-packed -> `upx -d` (fast, exact).
  2. Otherwise, if the binary still looks packed (packer signature, entropy
     > 7, no imports) -> Qiling emulation, OEP detection, memory dump.
  3. Not packed -> normalized.bin is a plain copy of the input.

Usage:
  python unpack.py <binary> --output <normalized.bin> [--method auto|upx|qiling|none]
                   [--rootfs DIR]
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import config
from binutil import load_binary, shannon_entropy
from detect import detect_packer_signature


def is_upx_packed(binary_path) -> bool:
    data = Path(binary_path).read_bytes()
    if b"UPX!" in data[:0x400] or b"UPX!" in data[-0x400:]:
        return True
    info = load_binary(binary_path)
    return any(s.name in ("UPX0", "UPX1") for s in info.sections)


def looks_packed(binary_path) -> bool:
    info = load_binary(binary_path)
    return bool(detect_packer_signature(info)) or shannon_entropy(info.data) > config.ENTROPY_THRESHOLD \
        or (info.fmt in ("elf", "pe") and not info.imports and not info.functions)


def upx_unpack(binary_path, output_path) -> bool:
    """Run `upx -d`; True on success."""
    if shutil.which(config.UPX_BIN) is None:
        return False
    out = Path(output_path)
    if out.exists():
        out.unlink()
    r = subprocess.run([config.UPX_BIN, "-d", "-q", "-o", str(out), str(binary_path)],
                       capture_output=True, text=True)
    return r.returncode == 0 and out.exists()


def qiling_unpack(binary_path, output_path, rootfs: str | None = None) -> dict:
    from qiling_scripts.dump_unpacked import find_oep_and_dump
    info = load_binary(binary_path)
    rootfs = rootfs or config.default_rootfs(info.os_type, info.arch)
    return find_oep_and_dump(str(binary_path), rootfs, str(output_path),
                             timeout_us=config.QILING_TIMEOUT_US)


def unpack_binary(binary_path, output_path, rootfs: str | None = None,
                  method: str = "auto", report: dict | None = None) -> Path:
    """Write the unpacked binary to `output_path` and return its Path.

    `report` (optional dict) receives {"method": ..., "details": ...}.
    """
    binary_path, output_path = Path(binary_path), Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = report if report is not None else {}
    report.update(method="none", details={})

    def copy_through():
        if binary_path.resolve() != output_path.resolve():
            shutil.copyfile(binary_path, output_path)
        return output_path

    if method == "none":
        return copy_through()

    if method in ("auto", "upx") and is_upx_packed(binary_path):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "unpacked.bin"
            if upx_unpack(binary_path, tmp):
                shutil.copyfile(tmp, output_path)
                report.update(method="upx")
                return output_path
        report["details"]["upx_error"] = "upx -d failed (modified / custom UPX?)"
        if method == "upx":
            raise RuntimeError("upx -d failed")

    if method == "qiling" or (method == "auto" and looks_packed(binary_path)):
        try:
            det = qiling_unpack(binary_path, output_path, rootfs)
            report.update(method="qiling", details={**report["details"], **det})
            return output_path
        except Exception as exc:  # emulation failure -> keep the original
            report["details"]["qiling_error"] = str(exc)
            if method == "qiling":
                raise
    return copy_through()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary")
    ap.add_argument("--output", "-o", required=True)
    ap.add_argument("--method", choices=["auto", "upx", "qiling", "none"], default="auto")
    ap.add_argument("--rootfs", default=None)
    a = ap.parse_args()
    rep: dict = {}
    out = unpack_binary(a.binary, a.output, a.rootfs, a.method, rep)
    print(f"[UNPACK] {a.binary} -> {out}  method={rep['method']}")
    if rep["details"]:
        print(json.dumps(rep["details"], indent=2, default=str))
