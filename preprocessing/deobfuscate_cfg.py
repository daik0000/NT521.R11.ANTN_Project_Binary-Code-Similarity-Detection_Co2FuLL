"""STEP 0.2c — CFG deobfuscation + pseudocode export (design section 5.4).

  1. Pre-pass (cff_unflatten.py): patch away OLLVM control-flow flattening
     and locate BCF opaque-predicate globals  -> <out>/deobfuscated.bin
  2. Ghidra headless (ghidra_scripts/deobfuscate_headless.py):
     auto-analysis, opaque globals -> read-only zero memory, label recovered
     import slots, decompile every function -> clean_pseudocode/<addr>.c

Differences from the design draft:
  * `-noanalysis` + `analyzeAll()` and the invalid `-analyzeHeadless` flag
    were replaced by Ghidra's normal headless auto-analysis.
  * The Ghidra script is Jython 2.7 (no f-strings).
  * The ghidra-deobfuscator/OllvmDeflat script mentioned in the draft is not
    used; unflattening is done by our own pre-pass (design option 2).

Usage:
  python deobfuscate_cfg.py <binary> <pseudocode_out_dir> [--no-unflatten]
                            [--imports recovered_imports.json]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import config
from binutil import load_binary
from cff_unflatten import unflatten_binary

SCRIPT_DIR = Path(__file__).resolve().parent / "ghidra_scripts"
SCRIPT_NAME = "deobfuscate_headless.py"


def analyze_headless_path(ghidra_home: str | None = None) -> Path:
    home = Path(ghidra_home or config.GHIDRA_HOME or "")
    exe = home / "support" / ("analyzeHeadless.bat" if os.name == "nt" else "analyzeHeadless")
    if not exe.exists():
        raise FileNotFoundError(f"analyzeHeadless not found under GHIDRA_HOME={home!s} "
                                "(set GHIDRA_HOME or run setup.sh)")
    return exe


def run_ghidra_export(binary_path, output_dir, preproc_config: dict | None = None,
                      timeout: int | None = None, log_path=None) -> dict:
    """Import `binary_path` into a throw-away project and export pseudocode."""
    output_dir = Path(output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    exe = analyze_headless_path()
    project_dir = tempfile.mkdtemp(prefix="ghidra_proj_")
    cfg_file = Path(project_dir) / "preproc_config.json"
    cfg_file.write_text(json.dumps(preproc_config or {}))
    log_path = Path(log_path) if log_path else output_dir.parent / f"ghidra_{output_dir.name}.log"

    cmd = ["bash", str(exe)] if os.name != "nt" else [str(exe)]
    cmd += [project_dir, f"preproc_{Path(binary_path).name}",
            "-import", str(Path(binary_path).resolve()),
            "-postScript", SCRIPT_NAME,
            "-scriptPath", str(SCRIPT_DIR),
            "-scriptlog", str(log_path.with_suffix(".script.log")),
            "-deleteProject"]
    env = os.environ.copy()
    env["GHIDRA_OUTPUT_DIR"] = str(output_dir.resolve())
    env["GHIDRA_PREPROC_CONFIG"] = str(cfg_file)
    env["GHIDRA_DECOMPILE_TIMEOUT"] = str(config.GHIDRA_DECOMPILE_TIMEOUT)
    try:
        r = subprocess.run(cmd, env=env, timeout=timeout or config.GHIDRA_TIMEOUT,
                           capture_output=True, text=True)
        log_path.write_text(r.stdout + "\n----- stderr -----\n" + r.stderr)
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)

    index_file = output_dir / "index.json"
    if not index_file.exists():
        raise RuntimeError(f"Ghidra export failed (rc={r.returncode}); see {log_path}")
    return json.loads(index_file.read_text())


def run_ghidra_deobfuscate(binary_path, output_dir, recovered_imports: dict | None = None,
                           unflatten: bool = True, report: dict | None = None) -> Path:
    """Design API: deobfuscate `binary_path` and write pseudocode to `output_dir`.

    Returns the path of the binary that was decompiled (patched or original).
    """
    output_dir = Path(output_dir)
    report = report if report is not None else {}
    info = load_binary(binary_path)
    target = Path(binary_path)
    opaque: list = []
    if unflatten:
        patched = output_dir.parent / "deobfuscated.bin"
        rep = unflatten_binary(binary_path, patched)
        report["unflatten"] = rep
        if rep.get("supported"):
            target, opaque = patched, rep["opaque_globals"]

    cfg = {"link_base": hex(info.image_base), "opaque_globals": opaque,
           "imports": recovered_imports or {}}
    idx = run_ghidra_export(target, output_dir, cfg)
    report["ghidra"] = {k: v for k, v in idx.items() if k != "functions"}
    report["ghidra"]["functions_exported"] = sum(1 for f in idx["functions"] if "error" not in f)
    return target


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary")
    ap.add_argument("output_dir")
    ap.add_argument("--no-unflatten", action="store_true",
                    help="only decompile (baseline pseudocode, no deobfuscation)")
    ap.add_argument("--imports", help="recovered_imports.json to label in Ghidra")
    a = ap.parse_args()
    imps = json.loads(Path(a.imports).read_text()) if a.imports else None
    rep: dict = {}
    run_ghidra_deobfuscate(a.binary, a.output_dir, imps, not a.no_unflatten, rep)
    print(json.dumps(rep, indent=2, default=str))
