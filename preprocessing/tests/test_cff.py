"""STEP 0.2c pre-pass — CFF unflattening + BCF opaque-global detection.

Strongest check: the patched binary must behave exactly like the original
(same stdout for several inputs), while the flattening dispatcher is no
longer reachable from any function entry.
"""
import io

import pytest
from capstone.x86 import X86_OP_IMM
from elftools.elf.elffile import ELFFile

from binutil import capstone_for, load_binary
from cff_unflatten import _is_state_constant, build_cfg, unflatten_binary
from conftest import FLATTENED_FUNCS, sample
from detect import analyze_signals


@pytest.fixture(scope="module")
def unflattened(tmp_path_factory):
    out = {}
    d = tmp_path_factory.mktemp("cff")
    for name in ("test_ollvm", "test_ollvm_sobf"):
        patched = d / f"{name}.deflat"
        out[name] = (patched, unflatten_binary(sample(name), patched))
    return out


def _bcf_symbols(path):
    with open(path, "rb") as f:
        st = ELFFile(f).get_section_by_name(".symtab")
        return {s["st_value"]: s.name for s in st.iter_symbols()
                if s.name.split(".")[0] in ("x", "y") and s["st_info"]["type"] == "STT_OBJECT"}


@pytest.mark.parametrize("name", ["test_ollvm", "test_ollvm_sobf"])
def test_all_flattened_functions_resolved(unflattened, name):
    _patched, rep = unflattened[name]
    funcs = {f["name"]: f for f in rep["functions"]}
    # OLLVM flattens at random (bcf decides which blocks exist) -> ask the detector
    expected = set(analyze_signals(sample(name))["metrics"]["cff_functions"])
    assert expected and expected <= set(funcs), f"detector {expected}, unflattener {set(funcs)}"
    if name == "test_ollvm":
        assert FLATTENED_FUNCS <= set(funcs)
    for fname, f in funcs.items():
        assert f["unresolved_blocks"] == [], (fname, f)
        assert f["patched_blocks"] >= 3
    assert rep["patches"] >= 15


def test_opaque_globals_are_ollvm_bcf_vars(unflattened):
    _patched, rep = unflattened["test_ollvm"]
    syms = _bcf_symbols(sample("test_ollvm"))
    found = {int(a, 16) for a in rep["opaque_globals"]}
    assert found, "no opaque globals found"
    assert found <= set(syms), {hex(a) for a in found - set(syms)}
    assert len(found) >= 6       # every x/y that is actually referenced


def test_dispatcher_unreachable(unflattened):
    patched, _rep = unflattened["test_ollvm"]
    info = load_binary(patched)
    md = capstone_for(info)
    for fname in FLATTENED_FUNCS:
        start, size = info.functions[fname]
        blocks = build_cfg(md, info, start, start + size)
        reach, todo = set(), [start]
        while todo:
            a = todo.pop()
            if a in reach or a not in blocks:
                continue
            reach.add(a)
            todo.extend(blocks[a].succs)
        # dispatcher = state compared against a random constant *and branched on*
        # (a bare `sub reg, 0x6efcb973` is OLLVM -sub instruction substitution)
        state_cmps = []
        for a in reach:
            ins = blocks[a].insns
            for k, i in enumerate(ins):
                if i.mnemonic in ("cmp", "sub") and len(i.operands) == 2 \
                        and i.operands[1].type == X86_OP_IMM and _is_state_constant(i.operands[1].imm) \
                        and any(n.mnemonic in ("je", "jne") for n in ins[k + 1:k + 3]):
                    state_cmps.append(hex(i.address))
        assert not state_cmps, f"{fname}: dispatcher still reachable at {state_cmps}"


def test_clean_binary_untouched(tmp_path):
    out = tmp_path / "clean.deflat"
    rep = unflatten_binary(sample("test_clean_O0"), out)
    assert rep["functions"] == [] and rep["patches"] == 0
    assert out.read_bytes() == sample("test_clean_O0").read_bytes()


def test_patched_layout_preserved(unflattened):
    patched, _ = unflattened["test_ollvm"]
    a, b = patched.read_bytes(), sample("test_ollvm").read_bytes()
    assert len(a) == len(b)
    ea, eb = ELFFile(io.BytesIO(a)), ELFFile(io.BytesIO(b))
    assert ea.get_section_by_name(".rodata").data() == eb.get_section_by_name(".rodata").data()


@pytest.mark.qiling
@pytest.mark.parametrize("name", ["test_ollvm", "test_ollvm_sobf"])
@pytest.mark.parametrize("argv", [[], ["a"], ["a", "b"], ["a", "b", "c", "d"]])
def test_semantics_preserved(unflattened, rootfs, name, argv):
    """argc changes classify()'s input -> exercises the even/odd branches."""
    from qiling_scripts.common import run_and_capture
    patched, _ = unflattened[name]
    expected = run_and_capture(str(sample(name)), rootfs, argv)
    got = run_and_capture(str(patched), rootfs, argv)
    assert b"classify:" in expected
    assert got == expected
