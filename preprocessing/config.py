"""Central configuration for the stage-0 preprocessing pipeline.

Every value can be overridden with an environment variable of the same name.
"""
import os
from pathlib import Path

PREPROC_DIR = Path(__file__).resolve().parent

# --- Ghidra -------------------------------------------------------------------
_default_ghidra = next(iter(sorted((PREPROC_DIR / "tools").glob("ghidra_*_PUBLIC"))), None)
GHIDRA_HOME = os.environ.get("GHIDRA_HOME") or (str(_default_ghidra) if _default_ghidra else "")
GHIDRA_TIMEOUT = int(os.environ.get("GHIDRA_TIMEOUT", "600"))          # seconds per binary
GHIDRA_DECOMPILE_TIMEOUT = int(os.environ.get("GHIDRA_DECOMPILE_TIMEOUT", "60"))  # per function

# --- Qiling -------------------------------------------------------------------
QILING_ROOTFS_DIR = Path(os.environ.get("QILING_ROOTFS_DIR", PREPROC_DIR / "qiling_rootfs"))

# Preferred rootfs per (os, arch). The first existing directory wins.
# x8664_linux_glibc236 is built by setup.sh from Debian 12 (glibc 2.36): the
# stock qiling rootfs ships glibc 2.27-era libs that cannot load binaries
# linked against GLIBC_2.34+ symbols.
QILING_ROOTFS_CANDIDATES = {
    ("linux", "x86_64"): ["x8664_linux_glibc236", "x8664_linux"],
    ("linux", "x86"): ["x86_linux_glibc236", "x86_linux"],
    ("linux", "arm"): ["arm_linux"],
    ("linux", "arm64"): ["arm64_linux"],
    ("linux", "mips"): ["mips32el_linux", "mips32_linux"],
    ("windows", "x86_64"): ["x8664_windows"],
    ("windows", "x86"): ["x86_windows"],
}

QILING_TIMEOUT_US = int(os.environ.get("QILING_TIMEOUT_US", str(60_000_000)))  # 60 s emulation budget

# --- External tools -----------------------------------------------------------
UPX_BIN = os.environ.get("UPX_BIN", "upx")
FLOSS_BIN = os.environ.get("FLOSS_BIN", "floss")

# --- Detection thresholds (section 5.1) --------------------------------------
ENTROPY_THRESHOLD = 7.0
MIN_IMPORTS = 5
STRING_DENSITY_THRESHOLD = 0.05
CFF_MIN_STATE_CONSTANTS = 6     # distinct random-looking constants compared in one function
BCF_MIN_PREDICATES = 2          # opaque-predicate shaped sequences


def default_rootfs(os_type: str, arch: str) -> str:
    """Return the best available Qiling rootfs for (os_type, arch)."""
    for name in QILING_ROOTFS_CANDIDATES.get((os_type, arch), []):
        p = QILING_ROOTFS_DIR / name
        if p.is_dir():
            return str(p)
    return str(QILING_ROOTFS_DIR)
