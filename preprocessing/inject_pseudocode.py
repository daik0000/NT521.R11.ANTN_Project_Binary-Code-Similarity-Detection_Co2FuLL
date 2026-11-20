"""Design 6.2 — prefer deobfuscated Ghidra pseudocode for LLM verification."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable


def get_clean_pseudocode(func_addr: int, clean_pseudo_dir: str,
                         fallback_func: Callable[[int], str]) -> str:
    """Pseudocode from clean_pseudocode/<addr>.c if present, else the fallback."""
    clean_path = os.path.join(clean_pseudo_dir, f"{func_addr:#010x}.c")
    if os.path.exists(clean_path):
        with open(clean_path, encoding="utf-8") as f:
            return f.read()
    return fallback_func(func_addr)


def load_index(clean_pseudo_dir: str) -> dict:
    """{address(int): entry} from the index.json written by the Ghidra script."""
    p = Path(clean_pseudo_dir) / "index.json"
    if not p.exists():
        return {}
    return {int(f["address"], 16): f for f in json.loads(p.read_text())["functions"]}


def get_clean_pseudocode_by_name(name: str, clean_pseudo_dir: str) -> str | None:
    for addr, entry in load_index(clean_pseudo_dir).items():
        if entry["name"] == name and "error" not in entry:
            return (Path(clean_pseudo_dir) / entry["file"]).read_text(encoding="utf-8")
    return None
