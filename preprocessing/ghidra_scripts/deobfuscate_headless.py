# Ghidra headless post-script: BCF cleanup + import labelling + pseudocode export.
# @category Co2FuLL.Preprocessing
# @runtime Jython
#
# Runs inside Ghidra's Jython 2.7 interpreter (no f-strings, no pathlib).
# Inputs (environment):
#   GHIDRA_OUTPUT_DIR      directory that receives <addr>.c files + index.json
#   GHIDRA_PREPROC_CONFIG  optional JSON:
#       {"link_base": "0x400000",            # link-time image base of the input
#        "opaque_globals": ["0x40405c", ...], # never-written BCF globals (from cff_unflatten)
#        "imports": {"0x4040a0": "puts", ...}}# recovered dynamic imports
#
# Steps
#   1. Opaque predicates (OLLVM -bcf): move each opaque global into its own
#      memory block, initialise it with 0 and make it read-only. Ghidra's
#      decompiler treats read-only memory as constant, folds
#      `y < 10 || x*(x-1) % 2 == 0` to true and drops the bogus branch.
#   2. Recovered imports: label the pointer slots (`ptr_<api>`) so indirect
#      calls read `(*ptr_puts)(...)` in the pseudocode.
#   3. Decompile every non-external, non-thunk function and write
#      <link-time address>.c (format "0x%08x.c", as in the design doc).

import os
import json
import codecs

from ghidra.app.decompiler import DecompInterface, DecompileOptions
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.program.model.data import PointerDataType

out_dir = os.environ.get("GHIDRA_OUTPUT_DIR", "/tmp/ghidra_output")
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

cfg = {}
cfg_path = os.environ.get("GHIDRA_PREPROC_CONFIG")
if cfg_path and os.path.exists(cfg_path):
    with open(cfg_path) as fh:
        cfg = json.load(fh)

program = currentProgram
monitor = ConsoleTaskMonitor()
mem = program.getMemory()
space = program.getAddressFactory().getDefaultAddressSpace()
image_base = program.getImageBase().getOffset()
link_base = int(cfg.get("link_base", hex(image_base)), 16)
delta = image_base - link_base


def to_addr(va):
    return space.getAddress(va + delta)


def log(msg):
    print("[preproc] " + msg)


# ----------------------------------------------------------------------------- 1. BCF
def make_readonly_zero(start_va, end_va):
    start, last = to_addr(start_va), to_addr(end_va - 1)
    blk = mem.getBlock(start)
    if blk is None:
        log("opaque global %#x not in memory" % start_va)
        return False
    if not blk.getStart().equals(start):
        mem.split(blk, start)
        blk = mem.getBlock(start)
    if blk.getEnd().compareTo(last) > 0:
        mem.split(blk, last.add(1))
        blk = mem.getBlock(start)
    if not blk.isInitialized():
        blk = mem.convertToInitialized(blk, 0)
    blk.setWrite(False)
    blk.setName("opaque_%x" % start_va)
    return True


opaque = sorted(int(a, 16) for a in cfg.get("opaque_globals", []))
ranges = []
for a in opaque:
    if ranges and ranges[-1][1] == a:
        ranges[-1][1] = a + 4
    else:
        ranges.append([a, a + 4])
n_opaque = 0
for s, e in ranges:
    try:
        if make_readonly_zero(s, e):
            n_opaque += 1
    except Exception as exc:  # keep going: worst case the predicate stays visible
        log("could not make %#x-%#x read-only: %s" % (s, e, exc))
log("opaque global ranges made read-only: %d" % n_opaque)

# ----------------------------------------------------------------------------- 2. imports
n_labels = 0
for addr_s, api in sorted(cfg.get("imports", {}).items()):
    try:
        addr = to_addr(int(addr_s, 16))
        blk = mem.getBlock(addr)
        if blk is None or blk.isExecute():
            continue                        # call sites: nothing to label
        listing = program.getListing()
        ptr = PointerDataType(program.getDataTypeManager())
        listing.clearCodeUnits(addr, addr.add(ptr.getLength() - 1), False)
        listing.createData(addr, ptr)
        createLabel(addr, "ptr_" + api, True)   # primary label; original symbol is kept
        n_labels += 1
    except Exception as exc:
        log("label %s @ %s failed: %s" % (api, addr_s, exc))
log("import slot labels: %d" % n_labels)

# ----------------------------------------------------------------------------- 3. export
opts = DecompileOptions()
decomp = DecompInterface()
decomp.setOptions(opts)
decomp.toggleCCode(True)
decomp.toggleSyntaxTree(True)
decomp.setSimplificationStyle("decompile")
decomp.openProgram(program)

timeout = int(os.environ.get("GHIDRA_DECOMPILE_TIMEOUT", "60"))
index = []
n_ok = 0
for func in program.getFunctionManager().getFunctions(True):
    if func.isExternal() or func.isThunk():
        continue
    va = func.getEntryPoint().getOffset() - delta
    fname = "0x%08x.c" % va
    entry = {"address": "0x%x" % va, "name": func.getName(), "file": fname,
             "size": func.getBody().getNumAddresses()}
    try:
        res = decomp.decompileFunction(func, timeout, monitor)
        if res is None or not res.decompileCompleted() or res.getDecompiledFunction() is None:
            entry["error"] = res.getErrorMessage() if res is not None else "no result"
            index.append(entry)
            continue
        code = res.getDecompiledFunction().getC()
        with codecs.open(os.path.join(out_dir, fname), "w", "utf-8") as fh:
            fh.write(code)
        called = sorted(set(f.getName() for f in func.getCalledFunctions(monitor)))
        entry.update(lines=len(code.splitlines()), calls=called)
        n_ok += 1
    except Exception as exc:
        entry["error"] = str(exc)
        log("decompile failed for %s: %s" % (func.getName(), exc))
    index.append(entry)

with codecs.open(os.path.join(out_dir, "index.json"), "w", "utf-8") as fh:
    json.dump({"program": program.getName(), "image_base": "0x%x" % image_base,
               "link_base": "0x%x" % link_base, "opaque_ranges": n_opaque,
               "import_labels": n_labels, "functions": index}, fh, indent=2)

decomp.dispose()
log("exported %d functions to %s" % (n_ok, out_dir))
