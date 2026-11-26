"""Design 6.1 — merge recovered imports / strings into Co2FuLL's feature dict.

Co2FuLL itself is not modified: call `merge_recovered_data` on the features
dict produced by the IDA scripts *before* the dependency graph is built.
"""
from __future__ import annotations

import json
from pathlib import Path


def merge_recovered_data(ida_features: dict, recovered_imports_path: str,
                         recovered_strings_path: str) -> dict:
    """Return `ida_features` with recovered imports/strings added (in place).

    * imports: dict {addr: name} is updated; a list of names is extended.
    * strings: list is extended with strings not already present.
    """
    extra_imports = json.loads(Path(recovered_imports_path).read_text()) \
        if Path(recovered_imports_path).exists() else {}
    extra_strings = json.loads(Path(recovered_strings_path).read_text()) \
        if Path(recovered_strings_path).exists() else []

    imports = ida_features.setdefault("imports", {})
    if isinstance(imports, dict):
        imports.update(extra_imports)
    else:
        imports.extend(n for n in dict.fromkeys(extra_imports.values()) if n not in imports)

    strings = ida_features.setdefault("strings", [])
    known = set(strings)
    strings.extend(s for s in extra_strings if s not in known)
    return ida_features


def merge_from_output_dir(ida_features: dict, stage0_dir: str) -> dict:
    """Convenience wrapper taking the per-binary stage-0 output directory."""
    d = Path(stage0_dir)
    return merge_recovered_data(ida_features, str(d / "recovered_imports.json"),
                                str(d / "recovered_strings.json"))
