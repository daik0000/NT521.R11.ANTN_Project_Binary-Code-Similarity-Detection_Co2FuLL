"""Helpers shared by the Qiling scripts."""
from __future__ import annotations

import os
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def staged_in_rootfs(binary_path: str, rootfs: str):
    """Copy the binary into <rootfs>/tmp/qiling_stage/ for the duration of the run.

    Qiling resolves guest paths (e.g. /proc/self/exe, which UPX's stub opens)
    relative to the rootfs, so the emulated program must live inside it.
    """
    stage_dir = Path(rootfs) / "tmp" / "qiling_stage"
    stage_dir.mkdir(parents=True, exist_ok=True)
    staged = stage_dir / f"{uuid.uuid4().hex[:8]}_{Path(binary_path).name}"
    shutil.copy2(binary_path, staged)
    os.chmod(staged, 0o755)
    try:
        yield str(staged.resolve())
    finally:
        try:
            staged.unlink()
        except OSError:
            pass


def new_qiling(binary_path: str, rootfs: str, verbose: bool = False, argv_extra=None,
               capture_stdout: bool = False):
    """Create a Qiling instance. The guest's stdout/stderr are discarded unless
    `verbose`; with `capture_stdout` they go to `ql.os.stdout` (SimpleOutStream,
    read it back with `.read()`)."""
    from qiling import Qiling
    from qiling.const import QL_VERBOSE
    from qiling.extensions import pipe

    ql = Qiling([binary_path] + list(argv_extra or []), str(Path(rootfs).resolve()),
                verbose=QL_VERBOSE.DEFAULT if verbose else QL_VERBOSE.DISABLED,
                console=verbose)
    if capture_stdout or not verbose:
        # in-memory streams (NullOutStream lacks attributes some syscalls need)
        ql.os.stdout = pipe.SimpleOutStream(1)
        if not verbose:
            ql.os.stderr = pipe.SimpleOutStream(2)
    return ql


def run_and_capture(binary_path: str, rootfs: str, argv_extra=None,
                    timeout_us: int = 30_000_000) -> bytes:
    """Run a program under Qiling and return what it printed on stdout."""
    with staged_in_rootfs(binary_path, rootfs) as staged:
        ql = new_qiling(staged, rootfs, argv_extra=argv_extra, capture_stdout=True)
        ql.run(timeout=timeout_us)
        return ql.os.stdout.read()
