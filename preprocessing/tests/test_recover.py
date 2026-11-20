"""STEP 0.2b — design 8.2 'Test string recovery' + import recovery."""
import pytest

from binutil import extract_strings, load_binary
from conftest import HIDDEN_APIS, HIDDEN_STRINGS, SUBJECT_LITERALS, sample
from recover_imports import (parse_floss_output, recover_imports, recover_strings,
                             recover_strings_dynamic, recover_strings_floss)


def test_parse_floss_json():
    doc = ('{"strings": {"decoded_strings": [{"string": "abc1"}], '
           '"stack_strings": [{"string": "abc1"}, {"string": "xyz2"}], "tight_strings": []}}')
    assert parse_floss_output(doc) == ["abc1", "xyz2"]


def test_static_baseline():
    """Before recovery: hidden sample shows neither its APIs nor its messages."""
    hidden = load_binary(sample("test_hidden"))
    assert not HIDDEN_APIS & set(hidden.imports)
    static = set(extract_strings(hidden.data))
    assert not any(s in static for s in HIDDEN_STRINGS)
    sobf_static = set(extract_strings(sample("test_ollvm_sobf").read_bytes()))
    assert sum(lit in sobf_static for lit in SUBJECT_LITERALS) <= 1   # design: 0–1
    clean_static = set(extract_strings(sample("test_clean").read_bytes()))
    assert sum(lit in clean_static for lit in SUBJECT_LITERALS) >= 3  # design: >= 3


@pytest.mark.qiling
def test_dynamic_imports_hidden(rootfs):
    details = {}
    imports = recover_imports(sample("test_hidden"), rootfs, "linux", details)
    assert set(imports.values()) == HIDDEN_APIS
    assert details["libraries"] == ["libc.so.6"]
    # every API must be mapped to the global pointer it is stored in (p_<api>)
    from elftools.elf.elffile import ELFFile
    with open(sample("test_hidden"), "rb") as f:
        symtab = ELFFile(f).get_section_by_name(".symtab")
        pvars = {s.name[2:]: s["st_value"] for s in symtab.iter_symbols() if s.name.startswith("p_")}
    assert set(pvars) == HIDDEN_APIS
    for rec in details["records"]:
        assert int(rec["slots"][0], 16) == pvars[rec["api"]], rec


@pytest.mark.qiling
def test_dynamic_strings_sobf(rootfs):
    """OLLVM -sobf encrypts every literal; they appear after emulation."""
    rep = recover_strings_dynamic(sample("test_ollvm_sobf"), rootfs)
    assert rep["error"] is None
    recovered = set(rep["strings"])
    missing = [lit for lit in SUBJECT_LITERALS if lit not in recovered]
    assert not missing, missing


@pytest.mark.qiling
def test_dynamic_strings_hidden(rootfs):
    rep = recover_strings_dynamic(sample("test_hidden"), rootfs)
    assert set(HIDDEN_STRINGS) <= set(rep["strings"])
    assert HIDDEN_APIS <= set(rep["strings"])          # decoded API names too
    assert "Hello, hidden world!" in rep["stdout"]


@pytest.mark.slow
def test_floss_decodes_hidden_strings():
    floss = recover_strings_floss(sample("test_hidden"))
    if not floss:
        pytest.skip("floss not installed")
    assert "Hello, hidden world!" in floss
    assert "secret message decoded" in floss


@pytest.mark.slow
@pytest.mark.qiling
def test_recover_strings_merged(rootfs):
    details = {}
    merged = recover_strings(sample("test_hidden"), rootfs, details=details)
    assert len(merged) == len(set(merged))
    assert set(HIDDEN_STRINGS) <= set(merged)
