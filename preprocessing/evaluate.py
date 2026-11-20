"""Fill in the evaluation table of design section 8.3 automatically.

Runs stage 0 on the test samples (tests/bin, built by tests/build_samples.sh),
measures the before/after metrics and writes
    <out>/evaluation.md    human-readable tables (design 8.3 + details)
    <out>/evaluation.json  raw numbers (used by tests/test_pipeline.py)

Usage:
  python evaluate.py [--bin-dir tests/bin] [--out-dir output/evaluation] [--jobs 3]
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

PREPROC = Path(__file__).resolve().parent

SUBJECT_LITERALS = [
    "Hello, %s!", "sum=%d, product=%d", "classify: negative value", "classify: even value",
    "classify: odd value", "binary code similarity detection", "result=%d class=%d msg=%s",
    "BinKit",
]
FLATTENED_FUNCS = ["greet", "classify", "duplicate_message"]

# (sample, run_stage0 kwargs)
JOBS = {
    "test_clean": {},                                   # must bypass
    "test_clean_O0": {"force": True, "use_floss": False},  # same-compiler reference pseudocode
    "test_ollvm": {},
    "test_ollvm_sobf": {},
    "test_ollvm_upx": {},
    "test_hidden": {},
}


# ============================================================================ metrics
_HEX = re.compile(r"(-?)0x([0-9a-fA-F]+)")
_BCF_VAR = re.compile(r"(?<![\w.])[xy](?:[._]\d+)?(?![\w.(])")


def _is_state_constant(v: int) -> bool:
    v &= 0xFFFFFFFF
    return 0x100000 <= v <= 0xFFF00000 and 6 <= bin(v).count("1") <= 26


def pseudo_metrics(code: str) -> dict:
    body = [ln for ln in code.splitlines()
            if ln.strip() and not ln.strip().startswith(("/*", "//", "*"))]
    text = "\n".join(body)
    consts = set()
    for sign, digits in _HEX.findall(text):
        v = int(digits, 16)
        v = (-v) & 0xFFFFFFFF if sign else v
        if _is_state_constant(v) and len(digits) <= 8:
            consts.add(v)
    return {
        "lines": len(body),
        "if": len(re.findall(r"\bif\s*\(", text)),
        "loops": len(re.findall(r"\b(?:for|while)\s*\(", text)),
        "while_true": len(re.findall(r"while\s*\(\s*true\s*\)", text)),
        "state_constants": len(consts),
        "bcf_var_refs": len(_BCF_VAR.findall(text)),
    }


def function_pseudocode(pseudo_dir: Path) -> dict:
    """{name: (code, index_entry)} from a clean_pseudocode directory."""
    idx = pseudo_dir / "index.json"
    if not idx.exists():
        return {}
    out = {}
    for f in json.loads(idx.read_text())["functions"]:
        p = pseudo_dir / f["file"]
        if "error" not in f and p.exists():
            out[f["name"]] = (p.read_text(encoding="utf-8"), f)
    return out


# ============================================================================ runner
def _run_one(args):
    import sys
    sys.path.insert(0, str(PREPROC))
    from run_pipeline import run_stage0
    sample, bin_dir, out_dir, kwargs = args
    logs = []
    rep = run_stage0(Path(bin_dir) / sample, out_dir, echo=logs.append, **kwargs)
    return sample, rep, logs


def _run_raw_baseline(bin_dir: Path, out_dir: Path):
    """Pseudocode of the OLLVM binary *without* deobfuscation (the 'before' column)."""
    import sys
    sys.path.insert(0, str(PREPROC))
    from binutil import load_binary
    from deobfuscate_cfg import run_ghidra_export
    b = bin_dir / "test_ollvm"
    d = out_dir / "test_ollvm_raw"
    d.mkdir(parents=True, exist_ok=True)
    run_ghidra_export(b, d / "clean_pseudocode", {"link_base": hex(load_binary(b).image_base)})
    return "test_ollvm_raw", None, []


def run_all(bin_dir, out_dir, jobs: int = 3, skip_run: bool = False) -> dict:
    bin_dir, out_dir = Path(bin_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    reports, logs = {}, {}
    if not skip_run:
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(_run_one, (s, str(bin_dir), str(out_dir), kw)) for s, kw in JOBS.items()
                    if (bin_dir / s).exists()]
            futs.append(ex.submit(_run_raw_baseline, bin_dir, out_dir))
            for f in futs:
                s, rep, lg = f.result()
                logs[s] = lg
    for s in list(JOBS) + ["test_ollvm_raw"]:
        p = out_dir / s / "stage0_report.json"
        if p.exists():
            reports[s] = json.loads(p.read_text())
    result = collect(bin_dir, out_dir, reports)
    result["logs"] = logs
    (out_dir / "evaluation.json").write_text(json.dumps(result, indent=2, default=str))
    (out_dir / "evaluation.md").write_text(render_markdown(result))
    return result


# ============================================================================ collect
def collect(bin_dir: Path, out_dir: Path, reports: dict) -> dict:
    import sys
    sys.path.insert(0, str(PREPROC))
    from binutil import extract_strings, load_binary

    samples = {}
    for s, rep in reports.items():
        static = set(extract_strings((bin_dir / s).read_bytes())) if (bin_dir / s).exists() else set()
        rec_path = out_dir / s / "recovered_strings.json"
        recovered = set(json.loads(rec_path.read_text())) if rec_path.exists() else set()
        det = rep.get("detection", {})
        uf = rep.get("deobfuscation", {}).get("unflatten", {})
        static_imports = load_binary(bin_dir / s).meaningful_imports if (bin_dir / s).exists() else []
        samples[s] = {
            "status": rep.get("status"),
            "signals": [k for k, v in det.get("signals", {}).items() if v],
            "entropy": det.get("metrics", {}).get("entropy"),
            "entropy_after_unpack": rep.get("detection_after_unpack", {}).get("entropy"),
            "unpack_method": rep.get("unpack", {}).get("method"),
            "static_imports": static_imports,
            "recovered_apis": rep.get("imports", {}).get("apis", []),
            "literals_static": sum(lit in static for lit in SUBJECT_LITERALS),
            "literals_after": sum(lit in static or lit in recovered for lit in SUBJECT_LITERALS),
            "strings_recovered": rep.get("strings", {}).get("count", 0),
            "flattened": [f["name"] for f in uf.get("functions", [])],
            "patches": uf.get("patches", 0),
            "opaque_globals": len(uf.get("opaque_globals", [])),
            "elapsed_s": rep.get("elapsed_s"),
            "deobf_error": rep.get("deobfuscation", {}).get("error"),
        }

    # pseudocode comparison: clean_O0 vs OLLVM raw vs OLLVM deobfuscated
    variants = {"clean": "test_clean_O0", "raw": "test_ollvm_raw", "deobf": "test_ollvm",
                "deobf_sobf": "test_ollvm_sobf", "deobf_upx": "test_ollvm_upx"}
    codes = {k: function_pseudocode(out_dir / s / "clean_pseudocode") for k, s in variants.items()}
    funcs = {}
    for fn in FLATTENED_FUNCS:
        row = {}
        for k in variants:
            if fn in codes[k]:
                code, entry = codes[k][fn]
                row[k] = {**pseudo_metrics(code), "calls": entry.get("calls", [])}
        funcs[fn] = row
    hidden = function_pseudocode(out_dir / "test_hidden" / "clean_pseudocode")
    hidden_text = "\n".join(code for code, _entry in hidden.values())
    return {"samples": samples, "functions": funcs,
            "hidden_ptr_labels": sorted(set(re.findall(r"ptr_(\w+)", hidden_text)))}


# ============================================================================ report
def _ok(b: bool) -> str:
    return "✅" if b else "❌"


def criteria(result: dict) -> list:
    """Rows of the design 8.3 table: (criterion, clean, before, after, pass)."""
    S, F = result["samples"], result["functions"]
    rows = []
    if {"test_clean", "test_hidden"} <= S.keys():
        c = len(S["test_clean"]["static_imports"])
        b = len(S["test_hidden"]["static_imports"])
        a = len(set(S["test_hidden"]["static_imports"]) | set(S["test_hidden"]["recovered_apis"]))
        rows.append(("Số imports tĩnh tìm được (import hiding: test_hidden)", f"{c}", f"{b}",
                     f"{a} (sau recover)", c >= 5 and b < 5 and a >= 5))
    if {"test_clean", "test_ollvm_sobf"} <= S.keys():
        c = S["test_clean"]["literals_static"]
        b = S["test_ollvm_sobf"]["literals_static"]
        a = S["test_ollvm_sobf"]["literals_after"]
        rows.append(("Strings đọc được (/8 literal, OLLVM -sobf)", f"{c}", f"{b}", f"{a} (sau recover)",
                     c >= 3 and b <= 1 and a >= 3))
    if F and all("clean" in r and "raw" in r and "deobf" in r for r in F.values()):
        def structured(k):
            return all(r[k]["while_true"] == 0 and r[k]["state_constants"] == 0
                       and r[k]["bcf_var_refs"] == 0 for r in F.values())
        sc, sr, sd = structured("clean"), structured("raw"), structured("deobf")
        rows.append(("Pseudocode có cấu trúc rõ (greet/classify/duplicate_message)",
                     _ok(sc), _ok(sr) + " (dispatcher/state)", _ok(sd), sc and not sr and sd))
    if {"test_clean", "test_ollvm"} <= S.keys():
        c, b = S["test_clean"]["entropy"], S["test_ollvm"]["entropy"]
        rows.append(("File entropy", f"{c:.2f}", f"{b:.2f}", f"{b:.2f} (CFF không đổi entropy)",
                     c < 7.0 and b < 7.0))
    if "test_ollvm_upx" in S:
        b, a = S["test_ollvm_upx"]["entropy"], S["test_ollvm_upx"]["entropy_after_unpack"]
        rows.append(("Entropy sau unpack (test_ollvm_upx)", "—", f"{b:.2f}",
                     f"{a:.2f}" if a is not None else "n/a", a is not None and a < 7.0))
    return rows


def render_markdown(result: dict) -> str:
    L = ["# Stage-0 evaluation (design §8.3)", ""]
    L += ["| Tiêu chí | Bản clean (baseline) | Bản obfuscated trước xử lý | Sau xử lý | Pass? |",
          "|---|---|---|---|---|"]
    for name, c, b, a, ok in criteria(result):
        L.append(f"| {name} | {c} | {b} | {a} | {_ok(ok)} |")
    L += ["", "## Per-sample", "",
          "| Sample | Status | Signals | Entropy (→ after unpack) | Unpack | Static imports | "
          "Recovered APIs | Literals static → after | Flattened funcs | Patches | Opaque globals | Time (s) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s, r in result["samples"].items():
        ent = f"{r['entropy']}" + (f" → {r['entropy_after_unpack']}" if r["entropy_after_unpack"] else "")
        L.append(f"| {s} | {r['status']} | {', '.join(r['signals'])} | {ent} | {r['unpack_method'] or '—'} | "
                 f"{len(r['static_imports'])} | {', '.join(r['recovered_apis']) or '—'} | "
                 f"{r['literals_static']} → {r['literals_after']} | {', '.join(r['flattened']) or '—'} | "
                 f"{r['patches']} | {r['opaque_globals']} | {r['elapsed_s']} |")
    L += ["", "## Pseudocode per function (lines / if / loops / while(true) / state consts / BCF refs)", "",
          "| Function | clean -O0 | OLLVM raw | OLLVM deobf | -sobf deobf | UPX deobf | same calls as clean? |",
          "|---|---|---|---|---|---|---|"]
    for fn, row in result["functions"].items():
        def cell(k):
            m = row.get(k)
            return "—" if not m else (f"{m['lines']} / {m['if']} / {m['loops']} / {m['while_true']} / "
                                      f"{m['state_constants']} / {m['bcf_var_refs']}")
        same = row.get("clean", {}).get("calls") == row.get("deobf", {}).get("calls")
        L.append(f"| {fn} | {cell('clean')} | {cell('raw')} | {cell('deobf')} | {cell('deobf_sobf')} | "
                 f"{cell('deobf_upx')} | {_ok(same)} |")
    if result.get("hidden_ptr_labels"):
        L += ["", f"test_hidden pseudocode uses recovered import labels: "
                  f"{', '.join('ptr_' + n for n in result['hidden_ptr_labels'])}"]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bin-dir", default=str(PREPROC / "tests" / "bin"))
    ap.add_argument("--out-dir", default=str(PREPROC / "output" / "evaluation"))
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--skip-run", action="store_true", help="only re-collect existing outputs")
    a = ap.parse_args()
    res = run_all(a.bin_dir, a.out_dir, a.jobs, a.skip_run)
    print(render_markdown(res))
