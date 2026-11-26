"""STEP 0.2a — design 8.2 'Test unpack'."""
import io

import pytest
from elftools.elf.elffile import ELFFile

from binutil import load_binary, shannon_entropy
from conftest import sample
from unpack import is_upx_packed, unpack_binary


def _load_segments(path):
    """{vaddr: bytes} of every PT_LOAD's file content."""
    data = path.read_bytes()
    elf = ELFFile(io.BytesIO(data))
    return elf["e_entry"], {s["p_vaddr"]: data[s["p_offset"]:s["p_offset"] + s["p_filesz"]]
                            for s in elf.iter_segments() if s["p_type"] == "PT_LOAD"}


def test_not_packed_is_copied(tmp_path):
    rep = {}
    out = unpack_binary(sample("test_clean"), tmp_path / "n.bin", report=rep)
    assert rep["method"] == "none"
    assert out.read_bytes() == sample("test_clean").read_bytes()


def test_upx_unpack_restores_original(tmp_path, upx_bin):
    packed = sample("test_ollvm_upx")
    assert is_upx_packed(packed)
    rep = {}
    out = unpack_binary(packed, tmp_path / "normalized.bin", report=rep)
    assert rep["method"] == "upx"
    original = sample("test_ollvm")
    # design: "unpacked phải ~bằng ollvm" — upx -d is exact
    assert abs(out.stat().st_size - original.stat().st_size) <= 64
    assert _load_segments(out) == _load_segments(original)
    assert shannon_entropy(out.read_bytes()) < 7.0
    assert load_binary(out).fmt == "elf"


@pytest.mark.qiling
@pytest.mark.parametrize("packed,original", [
    ("test_ollvm_upx", "test_ollvm"),     # non-PIE
    ("test_clean_upx", "test_clean"),     # PIE (gcc default)
])
def test_qiling_generic_unpacker(tmp_path, rootfs, packed, original):
    """Force the emulation path (as for a custom packer): OEP + memory dump."""
    rep = {}
    out = unpack_binary(sample(packed), tmp_path / "dump.bin", rootfs, method="qiling", report=rep)
    assert rep["method"] == "qiling"
    entry_d, segs_d = _load_segments(out)
    entry_o, segs_o = _load_segments(sample(original))
    assert rep["details"]["oep_rva"] == entry_o, "OEP must be the original entry point"
    assert entry_d == entry_o
    assert segs_d.keys() == segs_o.keys()
    for va, blob in segs_o.items():
        if va == min(segs_o):            # first segment holds the ELF header we rewrite
            blob, got = blob[64:], segs_d[va][64:]
        else:
            got = segs_d[va]
        assert got == blob, f"segment {va:#x} differs"
    assert shannon_entropy(out.read_bytes()) < 7.0
