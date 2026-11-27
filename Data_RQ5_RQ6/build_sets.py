"""Build the RQ5/RQ6 binary sets A, B, C, D from Data_advance/selected_10_O0.

    A/<variant>/<bin>.elf.strip   obfuscated (sub/bcf/fla/all), stripped
    B/<bin>.elf.strip             clean, stripped
    C/<variant>/<bin>.elf.strip   A after stage 0 (--force)  -> feed to IDA like A
    D/<bin>.elf.strip             B after stage 0 (--force)  -> feed to IDA like B
    C|D/.../stage0/<bin>/         stage0_report.json, recovered_imports.json,
                                  recovered_strings.json, log.txt
    ground_truth/<variant>/<bin>.json   {"0x<addr>": {"name", "size"}} from the
                                        unstripped original (labels for pairs)
    summary.csv                   one row per C/D binary

No pseudocode is produced here: the team decompiles A-D with IDA Pro. Stage 0 is
therefore run without Ghidra (0.1 detect, 0.2a unpack, 0.2b import/string
recovery) followed by the binary-level part of 0.2c: CFF unflattening and BCF
opaque-load patching, so C/D are clean for any decompiler. Patches are in place,
so a function has the same address in A and C (and in B and D).

usage (repo root, stage-0 venv active):
    python Data_RQ5_RQ6/build_sets.py [--jobs 6]
Re-running skips binaries already finished.
"""
import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRE = ROOT / "preprocessing"
SRC = ROOT / "Data_advance/selected_10_O0"
OUT = ROOT / "Data_RQ5_RQ6"
OBF = ["sub", "bcf", "fla", "all"]


def set_dir(base: str, variant: str) -> Path:
    """A/B (raw) or C/D (stage 0) directory for a variant."""
    return OUT / base if variant == "clean" else OUT / base / variant


def ground_truth(elf: Path) -> dict:
    from elftools.elf.elffile import ELFFile
    with open(elf, "rb") as fh:
        st = ELFFile(fh).get_section_by_name(".symtab")
        return {hex(s["st_value"]): {"name": s.name, "size": s["st_size"]} for s in st.iter_symbols()
                if s["st_info"]["type"] == "STT_FUNC" and s["st_value"] and s["st_shndx"] != "SHN_UNDEF"}


def stage0_job(variant: str, raw_bin: str) -> dict:
    sys.path.insert(0, str(PRE))
    from cff_unflatten import unflatten_binary
    from run_pipeline import run_stage0

    raw_bin = Path(raw_bin)
    name = raw_bin.name
    out_dir = set_dir("D" if variant == "clean" else "C", variant)
    meta = out_dir / "stage0" / name
    out_bin = out_dir / name
    row = {"set": "D" if variant == "clean" else "C", "variant": variant, "binary": name}
    if (meta / "stage0_report.json").exists() and out_bin.exists():
        rep = json.loads((meta / "stage0_report.json").read_text())
        return {**row, **_summary(rep), "status": "skipped (done)"}
    t0 = time.time()
    shutil.rmtree(meta, ignore_errors=True)
    meta.mkdir(parents=True)
    try:
        with tempfile.TemporaryDirectory(prefix="rq56_") as tmp:
            logs = []
            rep = run_stage0(raw_bin, tmp, force=True, skip_ghidra=True, echo=logs.append)
            work = Path(tmp) / raw_bin.stem
            urep = unflatten_binary(work / "normalized.bin", out_bin)
            urep["input"], urep["output"] = "normalized.bin", str(out_bin.relative_to(OUT))
            rep["deobfuscation"] = {"unflatten": urep, "decompiler": "none (pseudocode: IDA, done by the team)"}
            rep["input"] = str(raw_bin.relative_to(OUT))
            rep["elapsed_s"] = round(time.time() - t0, 1)
            for f in ("recovered_imports.json", "recovered_strings.json"):
                if (work / f).exists():
                    shutil.copy2(work / f, meta / f)
            logs.append(f"  [0.2c] unflattened {sum(1 for f in urep['functions'] if f.get('flattened'))} functions "
                        f"({urep['patches']} patches), opaque globals {len(urep['opaque_globals'])}, "
                        f"opaque loads patched {urep.get('opaque_loads_patched', 0)}")
            (meta / "log.txt").write_text("\n".join(map(str, logs)) + "\n")
            (meta / "stage0_report.json").write_text(json.dumps(rep, indent=1, default=str))
        out_bin.chmod(0o755)
        return {**row, **_summary(rep), "status": "ok"}
    except Exception:
        (meta / "error.txt").write_text(traceback.format_exc())
        return {**row, "status": "ERROR " + traceback.format_exc().splitlines()[-1],
                "seconds": round(time.time() - t0, 1)}


def _summary(rep: dict) -> dict:
    det = rep.get("detection", {})
    uf = rep.get("deobfuscation", {}).get("unflatten", {})
    fl = [f for f in uf.get("functions", []) if f.get("flattened")]
    return {
        "detected_without_force": det.get("is_obfuscated"),
        "signals": " ".join(k for k, v in det.get("signals", {}).items() if v),
        "unpack": rep.get("unpack", {}).get("method"),
        "recovered_apis": len((rep.get("imports") or {}).get("apis") or []),
        "recovered_strings": (rep.get("strings") or {}).get("count"),
        "strings_runtime_only": (rep.get("strings") or {}).get("dynamic"),
        "flattened_funcs": len(fl),
        "flattened_fully_patched": sum(1 for f in fl if not f.get("unresolved_blocks")),
        "cff_patches": uf.get("patches"),
        "opaque_globals": len(uf.get("opaque_globals", [])),
        "opaque_loads_patched": uf.get("opaque_loads_patched", 0),
        "seconds": rep.get("elapsed_s"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()

    tasks = []
    for variant in ["clean"] + OBF:
        for elf in sorted((SRC / variant).glob("*.elf")):
            name = elf.name + ".strip"                      # BinKit/Co2FuLL naming
            raw = set_dir("B" if variant == "clean" else "A", variant) / name
            if not raw.exists():
                raw.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["strip", "--strip-all", "-o", str(raw), str(elf)], check=True)
            gt = OUT / "ground_truth" / variant / (name + ".json")
            if not gt.exists():
                gt.parent.mkdir(parents=True, exist_ok=True)
                gt.write_text(json.dumps(ground_truth(elf), indent=1))
            tasks.append((raw.stat().st_size, variant, str(raw)))
    tasks.sort(reverse=True)                                  # biggest first
    print(f"{len(tasks)} stage-0 jobs, {a.jobs} workers", flush=True)
    rows = []
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        futs = [ex.submit(stage0_job, v, r) for _s, v, r in tasks]
        for f in as_completed(futs):
            r = f.result()
            rows.append(r)
            print(f"[{time.strftime('%H:%M:%S')}] {r['set']} {r['variant']:5s} {r['binary']:58s} "
                  f"{r['status']}  flat={r.get('flattened_funcs')} opaque={r.get('opaque_globals')} "
                  f"{r.get('seconds')}s", flush=True)
    rows.sort(key=lambda r: (r["set"], OBF.index(r["variant"]) if r["variant"] in OBF else -1, r["binary"]))
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(OUT / "summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
