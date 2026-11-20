"""Shared fixtures for the stage-0 preprocessing tests.

Test binaries are produced by tests/build_samples.sh (OLLVM docker image +
UPX). Tests needing Qiling / Ghidra / FLOSS / UPX are skipped when the tool
is unavailable.

Markers:
  qiling  — emulation (≈5–30 s each)
  ghidra  — Ghidra headless (≈1.5 min per binary)
  slow    — FLOSS / full pipeline
Run fast tests only:  pytest -m "not ghidra and not slow"
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
PREPROC_DIR = TESTS_DIR.parent
BIN_DIR = TESTS_DIR / "bin"
sys.path.insert(0, str(PREPROC_DIR))

import config as pp_config  # noqa: E402

# literals of test_subject.c — what "readable strings" means in the evaluation
SUBJECT_LITERALS = [
    "Hello, %s!", "sum=%d, product=%d", "classify: negative value", "classify: even value",
    "classify: odd value", "binary code similarity detection", "result=%d class=%d msg=%s",
    "BinKit",
]
HIDDEN_APIS = {"puts", "malloc", "free", "strlen", "memset", "strcpy", "snprintf"}
HIDDEN_STRINGS = ["Hello, hidden world!", "secret message decoded", "value=%d"]
FLATTENED_FUNCS = {"greet", "classify", "duplicate_message"}


def pytest_configure(config):
    for m in ("qiling", "ghidra", "slow"):
        config.addinivalue_line("markers", f"{m}: see tests/conftest.py")


def sample(name: str) -> Path:
    p = BIN_DIR / name
    if not p.exists():
        pytest.skip(f"{p} missing — run: bash tests/build_samples.sh")
    return p


@pytest.fixture(scope="session")
def rootfs() -> str:
    r = pp_config.default_rootfs("linux", "x86_64")
    if not (Path(r) / "lib" / "x86_64-linux-gnu" / "libc.so.6").exists() and \
            not (Path(r) / "lib" / "libc.so.6").exists():
        pytest.skip("Qiling rootfs not installed — run setup.sh")
    try:
        import qiling  # noqa: F401
    except ImportError:
        pytest.skip("qiling not installed")
    return r


@pytest.fixture(scope="session")
def ghidra_home() -> str:
    home = pp_config.GHIDRA_HOME
    if not home or not (Path(home) / "support" / "analyzeHeadless").exists():
        pytest.skip("Ghidra not installed (GHIDRA_HOME)")
    if shutil.which("java") is None:
        pytest.skip("java not on PATH")
    return home


@pytest.fixture(scope="session")
def upx_bin() -> str:
    if shutil.which(pp_config.UPX_BIN) is None:
        pytest.skip("upx not installed")
    return pp_config.UPX_BIN


@pytest.fixture(scope="session")
def work_dir(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("stage0")
