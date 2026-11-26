"""STEP 0.1 — design 8.2 'Test detection': clean -> False, OLLVM -> True, packed -> True."""
import pytest

from conftest import sample
from detect import analyze_signals, check_obfuscation_signals


@pytest.mark.parametrize("name", ["test_clean", "test_clean_O0", "test_clean.exe"])
def test_clean_binaries_bypass(name):
    rep = analyze_signals(sample(name))
    assert rep["is_obfuscated"] is False, rep["signals"]
    assert check_obfuscation_signals(sample(name)) is False


@pytest.mark.parametrize("name,expected_signals", [
    ("test_ollvm", {"cff_pattern", "bcf_pattern"}),
    ("test_ollvm_sobf", {"cff_pattern", "bcf_pattern"}),
    ("test_ollvm.exe", {"cff_pattern", "bcf_pattern"}),
    ("test_ollvm_upx", {"high_entropy", "few_imports", "packer_signature"}),
    ("test_clean_upx", {"high_entropy", "few_imports", "packer_signature"}),
    ("test_hidden", {"few_imports"}),
])
def test_obfuscated_binaries_detected(name, expected_signals):
    rep = analyze_signals(sample(name))
    fired = {k for k, v in rep["signals"].items() if v}
    assert rep["is_obfuscated"] is True
    assert expected_signals <= fired, f"expected {expected_signals}, got {fired}"


def test_entropy_ranges():
    """Design table 8.3: clean < 7.0, OLLVM 'stays 6.x' (CFF does not raise entropy), packed > 7."""
    clean = analyze_signals(sample("test_clean"))["metrics"]["entropy"]
    ollvm = analyze_signals(sample("test_ollvm"))["metrics"]["entropy"]
    packed = analyze_signals(sample("test_ollvm_upx"))["metrics"]["entropy"]
    assert clean < 7.0 and ollvm < 7.0 and packed > 7.0


def test_cff_constants_counted_per_function():
    m = analyze_signals(sample("test_ollvm"))["metrics"]
    # classify() alone compares the state against >= 20 random constants
    assert m["cff_functions"].get("classify", 0) >= 20
    assert "main" not in m["cff_functions"]  # single basic block -> not flattened
