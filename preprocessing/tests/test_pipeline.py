"""End-to-end stage 0 (design 8.2 'Test CFG deobfuscation' + 8.3 criteria + section 6).

One session fixture runs evaluate.run_all() — the whole pipeline on every
sample, Ghidra included (~5–8 min) — and the tests assert on its results.
"""
import json

import pytest
from click.testing import CliRunner

from conftest import FLATTENED_FUNCS, HIDDEN_APIS, sample


# ---------------------------------------------------------------- fast CLI checks
def test_cli_clean_bypass(tmp_path):
    from run_pipeline import main
    r = CliRunner().invoke(main, [str(sample("test_clean")), "--output-dir", str(tmp_path)])
    assert r.exit_code == 0, r.output
    assert "[CLEAN]" in r.output and "bypass" in r.output
    out = tmp_path / "test_clean"
    assert sorted(p.name for p in out.iterdir()) == ["normalized.bin", "stage0_report.json"]
    assert (out / "normalized.bin").read_bytes() == sample("test_clean").read_bytes()


@pytest.mark.qiling
def test_cli_obfuscated_without_ghidra(tmp_path, rootfs):
    from run_pipeline import main
    r = CliRunner().invoke(main, [str(sample("test_hidden")), "--output-dir", str(tmp_path),
                                  "--skip-ghidra", "--no-floss"])
    assert r.exit_code == 0, r.output
    assert "[OBFUSCATED]" in r.output
    out = tmp_path / "test_hidden"
    imports = json.loads((out / "recovered_imports.json").read_text())
    assert set(imports.values()) == HIDDEN_APIS


# ---------------------------------------------------------------- full evaluation
@pytest.fixture(scope="session")
def evaluation(work_dir, rootfs, ghidra_home, upx_bin):
    from evaluate import run_all
    for s in ("test_clean", "test_clean_O0", "test_ollvm", "test_ollvm_sobf", "test_ollvm_upx",
              "test_hidden"):
        sample(s)
    res = run_all(sample("test_clean").parent, work_dir / "evaluation", jobs=3)
    print((work_dir / "evaluation" / "evaluation.md").read_text())
    return res, work_dir / "evaluation"


@pytest.mark.ghidra
@pytest.mark.slow
def test_obfuscated_outputs_exist(evaluation):
    res, out = evaluation
    assert res["samples"]["test_clean"]["status"] == "bypassed"
    for s in ("test_ollvm", "test_ollvm_sobf", "test_ollvm_upx", "test_hidden"):
        d = out / s
        assert res["samples"][s]["status"] == "normalized"
        assert res["samples"][s]["deobf_error"] is None
        for f in ("normalized.bin", "recovered_imports.json", "recovered_strings.json",
                  "stage0_report.json", "clean_pseudocode/index.json"):
            assert (d / f).exists(), f"{s}: {f} missing"
        assert len(list((d / "clean_pseudocode").glob("0x*.c"))) >= 5


@pytest.mark.ghidra
@pytest.mark.slow
def test_design_criteria_table(evaluation):
    from evaluate import criteria
    res, _ = evaluation
    rows = criteria(res)
    assert len(rows) == 5
    failed = [r for r in rows if not r[4]]
    assert not failed, failed


@pytest.mark.ghidra
@pytest.mark.slow
@pytest.mark.parametrize("fn", sorted(FLATTENED_FUNCS))
def test_pseudocode_close_to_clean(evaluation, fn):
    res, _ = evaluation
    row = res["functions"][fn]
    clean, raw, deobf = row["clean"], row["raw"], row["deobf"]
    # before: dispatcher state constants (+ BCF globals where bcf hit this function)
    assert raw["state_constants"] > 0
    assert raw["lines"] > clean["lines"]
    # after: no dispatcher, no opaque predicates, same control structure as clean.
    # Line count is only compared with the raw version: OLLVM's reg2mem (extra
    # stack locals) and -sub (`-(-1 - n)` for `n + 1`) are not undone, so
    # e.g. duplicate_message is 35 lines vs 10 in the clean build (raw: 90).
    assert deobf["while_true"] == 0
    assert deobf["state_constants"] == 0
    assert deobf["bcf_var_refs"] == 0
    assert deobf["lines"] <= raw["lines"] * 0.5
    assert deobf["calls"] == clean["calls"]
    assert deobf["if"] == clean["if"] and deobf["loops"] == clean["loops"]


@pytest.mark.ghidra
@pytest.mark.slow
@pytest.mark.parametrize("variant", ["deobf_sobf", "deobf_upx"])
def test_variants_also_clean(evaluation, variant):
    res, _ = evaluation
    for fn, row in res["functions"].items():
        m = row[variant]
        assert m["state_constants"] == 0 and m["bcf_var_refs"] == 0 and m["while_true"] == 0, (fn, m)


@pytest.mark.ghidra
@pytest.mark.slow
def test_hidden_imports_labelled_in_pseudocode(evaluation):
    res, _ = evaluation
    assert HIDDEN_APIS <= set(res["hidden_ptr_labels"])


@pytest.mark.ghidra
@pytest.mark.slow
def test_co2full_injection_helpers(evaluation):
    """Design section 6: merge recovered data / pick clean pseudocode."""
    from inject_context import merge_from_output_dir
    from inject_pseudocode import get_clean_pseudocode, get_clean_pseudocode_by_name, load_index
    _, out = evaluation
    d = out / "test_hidden"
    feats = merge_from_output_dir({"imports": {"0x401030": "dlsym"}, "strings": ["x"]}, str(d))
    assert HIDDEN_APIS <= set(feats["imports"].values())
    assert "Hello, hidden world!" in feats["strings"]
    feats2 = merge_from_output_dir({"imports": ["dlsym"], "strings": []}, str(d))
    assert HIDDEN_APIS <= set(feats2["imports"])

    pdir = out / "test_ollvm" / "clean_pseudocode"
    idx = load_index(str(pdir))
    addr = next(a for a, e in idx.items() if e["name"] == "classify")
    code = get_clean_pseudocode(addr, str(pdir), lambda a: "FALLBACK")
    assert "classify: odd value" in code
    assert get_clean_pseudocode(0xDEAD, str(pdir), lambda a: "FALLBACK") == "FALLBACK"
    assert get_clean_pseudocode_by_name("classify", str(pdir)) == code
