"""Stage-0 entry point: normalise one binary before Co2FuLL (design 5.5).

  0.1 detect  ->  [CLEAN] bypass  |  [OBFUSCATED] continue
  0.2a unpack ->  normalized.bin
  0.2b recover -> recovered_strings.json, recovered_imports.json
  0.2c deobfuscate (pre-pass + Ghidra) -> clean_pseudocode/<addr>.c

Everything that happened is summarised in <out>/stage0_report.json.

Examples:
  python run_pipeline.py sample.bin
  python run_pipeline.py sample.bin --force --output-dir ./output
  for f in binaries/*; do python run_pipeline.py "$f" --output-dir ./output; done
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import click

import config
from binutil import load_binary
from deobfuscate_cfg import run_ghidra_deobfuscate
from detect import analyze_signals
from recover_imports import recover_imports, recover_strings
from unpack import unpack_binary


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, default=str))


def run_stage0(binary_path, output_dir="./output", arch=None, os_type=None, rootfs=None,
               force=False, skip_ghidra=False, unflatten=True, use_floss=True,
               unpack_method="auto", echo=print) -> dict:
    """Programmatic version of the CLI; returns the stage-0 report."""
    t0 = time.time()
    binary_path = Path(binary_path)
    out = Path(output_dir) / binary_path.stem
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    info = load_binary(binary_path)
    arch = arch or info.arch
    os_type = os_type or info.os_type
    rootfs = rootfs or config.default_rootfs(os_type, arch)
    report: dict = {"input": str(binary_path), "arch": arch, "os_type": os_type,
                    "rootfs": rootfs, "forced": force}

    # --- STEP 0.1: detection ------------------------------------------------
    det = analyze_signals(binary_path)
    report["detection"] = det
    if not force and not det["is_obfuscated"]:
        echo(f"[CLEAN] {binary_path} — bypass preprocessing")
        shutil.copyfile(binary_path, out / "normalized.bin")
        report.update(status="bypassed", elapsed_s=round(time.time() - t0, 2))
        _dump(out / "stage0_report.json", report)
        return report
    fired = [k for k, v in det["signals"].items() if v]
    echo(f"[{'OBFUSCATED' if det['is_obfuscated'] else 'FORCED'}] {binary_path} "
         f"— running normalization (signals: {', '.join(fired) or 'none'})")

    # --- STEP 0.2a: unpack --------------------------------------------------
    unpack_rep: dict = {}
    normalized = unpack_binary(binary_path, out / "normalized.bin", rootfs, unpack_method, unpack_rep)
    report["unpack"] = unpack_rep
    report["detection_after_unpack"] = analyze_signals(normalized)["metrics"]
    echo(f"  [0.2a] unpack method: {unpack_rep['method']}")

    # --- STEP 0.2b: import & string recovery --------------------------------
    can_emulate = Path(rootfs).is_dir()
    sdet: dict = {}
    strings = recover_strings(normalized, rootfs if can_emulate else None,
                              use_floss=use_floss, details=sdet)
    imports: dict = {}
    idet: dict = {}
    if can_emulate:
        try:
            imports = recover_imports(normalized, rootfs, os_type, idet)
        except Exception as exc:
            idet["error"] = f"{type(exc).__name__}: {exc}"
    _dump(out / "recovered_strings.json", strings)
    _dump(out / "recovered_imports.json", imports)
    report["strings"] = {"count": len(strings), "floss": len(sdet.get("floss", [])),
                         "dynamic": len(sdet.get("dynamic", [])),
                         "dynamic_error": sdet.get("dynamic_error")}
    report["imports"] = {"count": len(imports), "apis": sorted(set(imports.values())),
                         "libraries": idet.get("libraries", []), "error": idet.get("error")}
    echo(f"  [0.2b] recovered {len(set(imports.values()))} APIs, {len(strings)} strings")

    # --- STEP 0.2c: CFG deobfuscation ---------------------------------------
    pseudo_dir = out / "clean_pseudocode"
    if skip_ghidra:
        report["deobfuscation"] = {"skipped": True}
    else:
        drep: dict = {}
        try:
            run_ghidra_deobfuscate(normalized, pseudo_dir, imports, unflatten, drep)
        except Exception as exc:
            drep["error"] = f"{type(exc).__name__}: {exc}"
        report["deobfuscation"] = drep
        uf = drep.get("unflatten", {})
        echo(f"  [0.2c] unflattened {len(uf.get('functions', []))} functions "
             f"({uf.get('patches', 0)} patches), opaque globals: {len(uf.get('opaque_globals', []))}"
             + (f"  ERROR: {drep['error']}" if "error" in drep else ""))

    report.update(status="normalized", elapsed_s=round(time.time() - t0, 2))
    _dump(out / "stage0_report.json", report)

    echo(f"[DONE] Output saved to: {out}")
    echo(f"  normalized binary : {normalized}")
    echo(f"  recovered imports : {len(set(imports.values()))} APIs")
    echo(f"  recovered strings : {len(strings)} strings")
    echo(f"  clean pseudocode  : {pseudo_dir if not skip_ghidra else '(skipped)'}")
    return report


@click.command(help=__doc__)
@click.argument("binary_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--arch", default=None, help="x86, x86_64, arm, arm64, mips (default: from headers)")
@click.option("--os-type", default=None, help="windows | linux (default: from headers)")
@click.option("--rootfs", default=None, help="Qiling rootfs (default: config.default_rootfs)")
@click.option("--output-dir", default="./output", show_default=True)
@click.option("--force", is_flag=True, help="Bỏ qua detection, chạy full pipeline")
@click.option("--skip-ghidra", is_flag=True, help="Skip step 0.2c (no pseudocode)")
@click.option("--no-unflatten", is_flag=True, help="Ghidra export without the CFF/BCF pre-pass")
@click.option("--no-floss", is_flag=True, help="Do not run FLOSS (faster)")
@click.option("--unpack-method", type=click.Choice(["auto", "upx", "qiling", "none"]), default="auto")
def main(binary_path, arch, os_type, rootfs, output_dir, force, skip_ghidra, no_unflatten,
         no_floss, unpack_method):
    run_stage0(binary_path, output_dir, arch, os_type, rootfs, force, skip_ghidra,
               not no_unflatten, not no_floss, unpack_method, echo=click.echo)


if __name__ == "__main__":
    main()
