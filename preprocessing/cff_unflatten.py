"""Control-flow-flattening removal pre-pass (OLLVM `-fla`) + BCF analysis.

Runs *before* Ghidra (design 5.4, "pre-pass" option) and produces a patched
binary whose CFG no longer goes through the flattening dispatcher.

Algorithm (per function, x86/x86-64):
  1. Recursive-descent disassembly (capstone) -> basic blocks + CFG.
  2. State variable S := the stack slot most often assigned random 32-bit
     constants (`mov dword [rbp-X], 0x4335ff95`).
  3. Dispatcher: loopEnd = block with the most predecessors; loopEntry = its
     jump target. Dispatcher blocks = blocks reachable from loopEntry that
     only load/copy/compare the state and branch.
  4. For each state constant C, emulate the dispatcher with unicorn (S := C)
     until execution leaves the dispatcher -> real successor block.
  5. Patch every block that "returns" to the dispatcher:
       mov [S], C ; jmp loopEnd                      ->  jmp succ(C)
       mov R,A ; mov R2,B ; <cmp> ; cmovCC R,R2 ;
       mov [S],R ; jmp loopEnd                        ->  <cmp> ; jCC succ(B) ; jmp succ(A)
     The dispatcher becomes dead code.

BCF (`-bcf`): the opaque predicates read global variables that are never
written (OLLVM's `x`/`y`, always 0). They are reported as `opaque_globals`;
the Ghidra script turns them into read-only zero-initialised memory so the
decompiler constant-folds the predicates and drops the bogus blocks.

Scope / limits: targets OLLVM-style flattening as emitted at -O0 (state in a
stack slot). Register-allocated state (-O2 builds), indirect dispatchers
(jump tables) and non-x86 architectures are reported as unsupported.

Usage:
  python cff_unflatten.py <in> <out> [--json]
"""
from __future__ import annotations

import json
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path

from binutil import BinaryInfo, capstone_for, load_binary

PAGE = 0x1000
STACK_BASE = 0x7FF00000
STACK_SIZE = 0x20000

JCC_OPCODE = {
    "o": 0x80, "no": 0x81, "b": 0x82, "c": 0x82, "nae": 0x82, "ae": 0x83, "nb": 0x83, "nc": 0x83,
    "e": 0x84, "z": 0x84, "ne": 0x85, "nz": 0x85, "be": 0x86, "na": 0x86, "a": 0x87, "nbe": 0x87,
    "s": 0x88, "ns": 0x89, "p": 0x8A, "pe": 0x8A, "np": 0x8B, "po": 0x8B, "l": 0x8C, "nge": 0x8C,
    "ge": 0x8D, "nl": 0x8D, "le": 0x8E, "ng": 0x8E, "g": 0x8F, "nle": 0x8F,
}


# ============================================================================ CFG
@dataclass
class Block:
    start: int
    insns: list = field(default_factory=list)
    succs: list = field(default_factory=list)
    preds: list = field(default_factory=list)

    @property
    def end(self) -> int:
        last = self.insns[-1]
        return last.address + last.size

    @property
    def last(self):
        return self.insns[-1]


def _is_state_constant(v: int) -> bool:
    v &= 0xFFFFFFFF
    if v < 0x100000 or v > 0xFFF00000:
        return False
    return 6 <= bin(v).count("1") <= 26


def _branch_target(ins):
    import capstone.x86 as x86
    if ins.operands and ins.operands[0].type == x86.X86_OP_IMM:
        return ins.operands[0].imm
    return None


def _is_jcc(ins) -> bool:
    return ins.mnemonic.startswith("j") and ins.mnemonic != "jmp"


def build_cfg(md, info: BinaryInfo, start: int, end: int) -> dict:
    """Recursive descent disassembly of [start, end) -> {addr: Block}."""
    code = info.read_va(start, end - start)
    if not code:
        return {}
    insn_at: dict = {}
    leaders = {start}
    todo = [start]
    while todo:
        a = todo.pop()
        while start <= a < end and a not in insn_at:
            off = a - start
            ins = next(md.disasm(code[off:off + 16], a, 1), None)
            if ins is None or ins.id == 0:
                break
            insn_at[a] = ins
            m = ins.mnemonic
            if m == "jmp":
                t = _branch_target(ins)
                if t is not None and start <= t < end:
                    leaders.add(t)
                    todo.append(t)
                break
            if _is_jcc(ins):
                t = _branch_target(ins)
                if t is not None and start <= t < end:
                    leaders.add(t)
                    todo.append(t)
                leaders.add(a + ins.size)
            if m in ("ret", "retn", "hlt", "ud2") or m.startswith("ret"):
                break
            a += ins.size

    blocks: dict = {}
    cur = None
    for a in sorted(insn_at):
        ins = insn_at[a]
        if cur is None or a in leaders or cur.end != a:
            cur = Block(a)
            blocks[a] = cur
        cur.insns.append(ins)
        m = ins.mnemonic
        if m == "jmp" or _is_jcc(ins) or m.startswith("ret") or m in ("hlt", "ud2"):
            cur = None
    for b in blocks.values():
        last = b.last
        m = last.mnemonic
        if m == "jmp":
            t = _branch_target(last)
            if t in blocks:
                b.succs.append(t)
        elif _is_jcc(last):
            t = _branch_target(last)
            if t in blocks:
                b.succs.append(t)
            if b.end in blocks:
                b.succs.append(b.end)
        elif not (m.startswith("ret") or m in ("hlt", "ud2")):
            if b.end in blocks:
                b.succs.append(b.end)
    for b in blocks.values():
        for s in b.succs:
            blocks[s].preds.append(b.start)
    return blocks


# ============================================================================ helpers
def _mem_key(op, ins):
    """(base_reg_name, disp) for a stack memory operand, else None."""
    import capstone.x86 as x86
    if op.type != x86.X86_OP_MEM or op.mem.index != 0:
        return None
    base = ins.reg_name(op.mem.base) if op.mem.base else None
    if base not in ("rbp", "ebp", "rsp", "esp"):
        return None
    return base, op.mem.disp


def _store_imm_to(ins, key=None):
    """If ins is `mov dword [stack], imm` (optionally to `key`) return imm."""
    import capstone.x86 as x86
    if ins.mnemonic != "mov" or len(ins.operands) != 2:
        return None
    dst, src = ins.operands
    if src.type != x86.X86_OP_IMM or dst.size != 4:
        return None
    k = _mem_key(dst, ins)
    if k is None or (key is not None and k != key):
        return None
    return src.imm & 0xFFFFFFFF


def _store_reg_to(ins, key):
    import capstone.x86 as x86
    if ins.mnemonic != "mov" or len(ins.operands) != 2:
        return None
    dst, src = ins.operands
    if src.type != x86.X86_OP_REG or _mem_key(dst, ins) != key:
        return None
    return src.reg


def _writes_slot(ins, key) -> bool:
    import capstone.x86 as x86
    if not ins.operands:
        return False
    op = ins.operands[0]
    return op.type == x86.X86_OP_MEM and _mem_key(op, ins) == key and ins.mnemonic not in ("cmp", "test")


def _regs_touched(ins):
    try:
        r, w = ins.regs_access()
        return set(r), set(w)
    except Exception:
        return set(), set()


def _reg_family(ins, reg) -> str:
    """eax/rax/ax/al -> 'a' ... so aliases compare equal."""
    n = ins.reg_name(reg)
    for fam in ("ax", "bx", "cx", "dx", "si", "di", "bp", "sp"):
        if n in (fam, "e" + fam, "r" + fam) or n == fam[0] + "l" and fam[1] == "x":
            return fam
    if n.startswith("r") and n[1:].rstrip("dwb").isdigit():
        return "r" + n[1:].rstrip("dwb")
    return n


# ============================================================================ emulator
class DispatcherEmulator:
    """Maps the binary into unicorn once; resolves state -> successor."""

    def __init__(self, info: BinaryInfo):
        import unicorn as uc
        import unicorn.x86_const as ux
        self.uc_mod, self.ux = uc, ux
        mode = uc.UC_MODE_64 if info.arch == "x86_64" else uc.UC_MODE_32
        self.mu = uc.Uc(uc.UC_ARCH_X86, mode)
        self.is64 = info.arch == "x86_64"
        pages = set()
        for s in info.segments:
            lo, hi = s.vaddr & ~(PAGE - 1), (s.vaddr + max(s.memsz, s.filesz) + PAGE - 1) & ~(PAGE - 1)
            pages.update(range(lo, hi, PAGE))
        for run_lo, run_hi in _runs(sorted(pages)):
            self.mu.mem_map(run_lo, run_hi - run_lo)
        for s in info.segments:
            if s.filesz:
                self.mu.mem_write(s.vaddr, info.data[s.offset:s.offset + s.filesz])
        self.mu.mem_map(STACK_BASE, STACK_SIZE)

    def resolve(self, entry: int, slot, value: int, dispatcher_addrs: set, limit: int = 4000):
        ux, mu = self.ux, self.mu
        frame = STACK_BASE + STACK_SIZE // 2
        regs = [ux.UC_X86_REG_RAX, ux.UC_X86_REG_RBX, ux.UC_X86_REG_RCX, ux.UC_X86_REG_RDX,
                ux.UC_X86_REG_RSI, ux.UC_X86_REG_RDI] if self.is64 else \
               [ux.UC_X86_REG_EAX, ux.UC_X86_REG_EBX, ux.UC_X86_REG_ECX, ux.UC_X86_REG_EDX,
                ux.UC_X86_REG_ESI, ux.UC_X86_REG_EDI]
        for r in regs:
            mu.reg_write(r, 0)
        bp = ux.UC_X86_REG_RBP if self.is64 else ux.UC_X86_REG_EBP
        sp = ux.UC_X86_REG_RSP if self.is64 else ux.UC_X86_REG_ESP
        mu.reg_write(bp, frame)
        mu.reg_write(sp, frame - 0x400)
        base, disp = slot
        addr = (frame if base in ("rbp", "ebp") else frame - 0x400) + disp
        mu.mem_write(addr, struct.pack("<I", value))
        result = {"target": None}

        def hook(_mu, address, _size, _ud):
            if address not in dispatcher_addrs:
                result["target"] = address
                _mu.emu_stop()

        h = mu.hook_add(self.uc_mod.UC_HOOK_CODE, hook)
        try:
            mu.emu_start(entry, 0, count=limit)
        except self.uc_mod.UcError:
            pass
        finally:
            mu.hook_del(h)
        return result["target"]


def _runs(pages):
    if not pages:
        return []
    out, lo, prev = [], pages[0], pages[0]
    for p in pages[1:]:
        if p != prev + PAGE:
            out.append((lo, prev + PAGE))
            lo = p
        prev = p
    out.append((lo, prev + PAGE))
    return out


# ============================================================================ per function
_DISPATCH_MNEMS = {"mov", "sub", "cmp", "jmp", "nop", "movsxd", "movzx"}


def _is_dispatcher_block(b: Block, slot) -> bool:
    import capstone.x86 as x86
    reads_state = False
    for ins in b.insns:
        m = ins.mnemonic
        if not (m in _DISPATCH_MNEMS or _is_jcc(ins)):
            return False
        if _writes_slot(ins, slot):
            return False
        for op in ins.operands:
            if op.type == x86.X86_OP_MEM:
                if _mem_key(op, ins) is None:      # only stack slots allowed
                    return False
                reads_state = True
        if m == "sub" and ins.operands and ins.operands[0].type != x86.X86_OP_REG:
            return False
    return reads_state or (len(b.insns) == 1 and b.last.mnemonic == "jmp")


def unflatten_function(md, info: BinaryInfo, emu: DispatcherEmulator, name: str,
                       start: int, end: int) -> tuple:
    """Return (report_dict, list_of_patches[(va, bytes)])."""
    rep = {"name": name, "address": hex(start), "flattened": False}
    blocks = build_cfg(md, info, start, end)
    if not blocks:
        rep["error"] = "no code"
        return rep, []

    # -- 1. state variable
    slot_counts = Counter()
    for b in blocks.values():
        for ins in b.insns:
            imm = _store_imm_to(ins)
            if imm is not None and _is_state_constant(imm):
                ops = ins.operands
                slot_counts[_mem_key(ops[0], ins)] += 1
    if not slot_counts:
        return rep, []
    slot, n_assign = slot_counts.most_common(1)[0]
    if n_assign < 2:
        return rep, []

    # -- 2. dispatcher
    loop_end = max(blocks.values(), key=lambda b: len(b.preds))
    if len(loop_end.preds) < 3:
        return rep, []
    if len(loop_end.insns) == 1 and loop_end.last.mnemonic == "jmp" and loop_end.succs:
        loop_entry = blocks[loop_end.succs[0]]
    else:
        loop_entry = loop_end
    dispatcher = {loop_end.start}
    work = [loop_entry.start]
    while work:
        a = work.pop()
        if a in dispatcher and a != loop_end.start:
            continue
        b = blocks[a]
        if not _is_dispatcher_block(b, slot):
            continue
        dispatcher.add(a)
        work.extend(s for s in b.succs if s not in dispatcher)
    if loop_entry.start not in dispatcher:
        rep["error"] = "loop entry is not a dispatcher block"
        return rep, []
    disp_addrs = {i.address for a in dispatcher for i in blocks[a].insns}
    rep.update(flattened=True, state_slot=f"{slot[0]}{slot[1]:+#x}",
               dispatcher_blocks=len(dispatcher), loop_entry=hex(loop_entry.start),
               loop_end=hex(loop_end.start))

    cache: dict = {}

    def succ(value):
        if value not in cache:
            t = emu.resolve(loop_entry.start, slot, value, disp_addrs)
            cache[value] = t if (t in blocks and t not in dispatcher) else None
        return cache[value]

    # -- 3. patch blocks that flow back into the dispatcher
    patches, n_ok, unresolved = [], 0, []
    to_dispatcher = {loop_end.start, loop_entry.start}
    for b in sorted(blocks.values(), key=lambda b: b.start):
        if b.start in dispatcher:
            continue
        last = b.last
        if last.mnemonic == "jmp" and _branch_target(last) in to_dispatcher:
            tail = b.insns[:-1]
        elif b.end in to_dispatcher and not (last.mnemonic == "jmp" or _is_jcc(last)
                                             or last.mnemonic.startswith("ret")):
            tail = b.insns
        else:
            continue
        region_end = b.end
        patch = _patch_unconditional(tail, slot, region_end, succ) or \
            _patch_conditional(tail, slot, region_end, succ)
        if patch:
            patches.append(patch)
            n_ok += 1
        else:
            unresolved.append(hex(b.start))
    rep.update(states=len(cache), patched_blocks=n_ok, unresolved_blocks=unresolved)
    return rep, patches


def _jmp(src: int, dst: int) -> bytes:
    return b"\xE9" + struct.pack("<i", dst - (src + 5))


def _jcc(src: int, dst: int, cc: str) -> bytes:
    return bytes([0x0F, JCC_OPCODE[cc]]) + struct.pack("<i", dst - (src + 6))


def _relocatable(ins) -> bool:
    """Instruction can be copied to another address unchanged."""
    import capstone.x86 as x86
    if ins.mnemonic.startswith(("j", "call", "loop", "ret")):
        return False
    return not any(op.type == x86.X86_OP_MEM and op.mem.base == x86.X86_REG_RIP
                   for op in ins.operands)


def _writes_flags(ins) -> bool:
    import capstone.x86 as x86
    _r, w = _regs_touched(ins)
    return x86.X86_REG_EFLAGS in w


def _split_at_state_store(tail, slot):
    """(head, store_insn, trailing) where store_insn is the last write of S.

    OLLVM sometimes schedules unrelated stores after the state update, e.g.
        mov [S], eax ; mov byte [rbp-0x1d], 0 ; jmp loopEnd
    """
    for k in range(len(tail) - 1, -1, -1):
        if _writes_slot(tail[k], slot):
            trailing = tail[k + 1:]
            if all(_relocatable(t) and not _writes_slot(t, slot) for t in trailing):
                return tail[:k], tail[k], trailing
            return None
    return None


def _patch_unconditional(tail, slot, region_end, succ):
    split = _split_at_state_store(tail, slot)
    if split is None:
        return None
    _head, store, trailing = split
    imm = _store_imm_to(store, slot)
    if imm is None:
        return None
    target = succ(imm)
    if target is None:
        return None
    at = store.address
    code = b"".join(bytes(t.bytes) for t in trailing)
    code += _jmp(at + len(code), target)
    if len(code) > region_end - at:
        return None
    return at, code + b"\x90" * (region_end - at - len(code))


def _patch_conditional(tail, slot, region_end, succ):
    import capstone.x86 as x86
    split = _split_at_state_store(tail, slot)
    if split is None:
        return None
    head, store, trailing = split
    if len(head) < 3 or any(_writes_flags(t) for t in trailing):
        return None
    reg_r = _store_reg_to(store, slot)
    cmov = head[-1]
    if reg_r is None or not cmov.mnemonic.startswith("cmov") or len(cmov.operands) != 2:
        return None
    if cmov.operands[0].type != x86.X86_OP_REG or cmov.operands[1].type != x86.X86_OP_REG:
        return None
    cc = cmov.mnemonic[4:]
    if cc not in JCC_OPCODE or cmov.operands[0].reg != reg_r:
        return None
    reg_r2 = cmov.operands[1].reg
    fam_r, fam_r2 = _reg_family(cmov, reg_r), _reg_family(cmov, reg_r2)

    mov_a = mov_b = None
    body = head[:-1]
    for idx in range(len(body) - 1, -1, -1):
        ins = body[idx]
        if ins.mnemonic == "mov" and len(ins.operands) == 2 and ins.operands[0].type == x86.X86_OP_REG \
                and ins.operands[1].type == x86.X86_OP_IMM:
            fam = _reg_family(ins, ins.operands[0].reg)
            if fam == fam_r and mov_a is None:
                mov_a = idx
            elif fam == fam_r2 and mov_b is None:
                mov_b = idx
        if mov_a is not None and mov_b is not None:
            break
    if mov_a is None or mov_b is None:
        return None
    val_a = body[mov_a].operands[1].imm & 0xFFFFFFFF
    val_b = body[mov_b].operands[1].imm & 0xFFFFFFFF
    first = min(mov_a, mov_b)
    middle = [ins for i, ins in enumerate(body[first:], first) if i not in (mov_a, mov_b)]
    for ins in middle + list(trailing):   # position independent, independent of R / R2
        if not _relocatable(ins):
            return None
        rd, wr = _regs_touched(ins)
        fams = {_reg_family(ins, r) for r in rd | wr}
        if fam_r in fams or fam_r2 in fams:
            return None
    t_true, t_false = succ(val_b), succ(val_a)
    if t_true is None or t_false is None:
        return None
    at = body[first].address
    code = b"".join(bytes(i.bytes) for i in middle + list(trailing))
    code += _jcc(at + len(code), t_true, cc)
    code += _jmp(at + len(code), t_false)
    if len(code) > region_end - at:
        return None
    return at, code + b"\x90" * (region_end - at - len(code))


# ============================================================================ BCF globals
_ARG_REGS = {"di", "si", "dx", "cx", "r8", "r9"}       # SysV x86-64 integer argument registers
_PREDICATE_WINDOW = 14


def _copy_reloc_ranges(info: BinaryInfo) -> list:
    """[(start, end)] covered by R_*_COPY relocations.

    Library data such as stdout/stderr/optarg is copied into the executable's .bss
    and written by libc, never by the program: it looks "read-only" to a scan of
    the program's own code but is not constant.
    """
    if info.fmt != "elf":
        return []
    import io
    from elftools.elf.elffile import ELFFile
    from elftools.elf.relocation import RelocationSection
    out = []
    try:
        elf = ELFFile(io.BytesIO(info.data))
        dynsym = elf.get_section_by_name(".dynsym")
        for sec in elf.iter_sections():
            if not isinstance(sec, RelocationSection):
                continue
            for r in sec.iter_relocations():
                if r["r_info_type"] != 5:                    # R_X86_64_COPY == R_386_COPY == 5
                    continue
                size = 0
                if dynsym is not None and r["r_info_sym"]:
                    size = dynsym.get_symbol(r["r_info_sym"])["st_size"]
                out.append((r["r_offset"], r["r_offset"] + (size or 8)))
    except Exception:
        pass
    return out


def _feeds_opaque_predicate(insns: list, i: int, dst: str) -> bool:
    """Does the value loaded into `dst` by insns[i] reach an OLLVM opaque predicate?

    Follows `dst` and its register copies for a few instructions and accepts only
      x * (x - 1) & 1   -> an `imul` on a tracked register, then `and`/`test` tracked, 1
      y < 10            -> `cmp tracked, 9|10`
    (OLLVM -bcf, see BogusControlFlow.cpp). The old heuristic accepted *any* imul or
    `cmp ..., 0xa` nearby, which let real globals (elf_header, ...) through.
    """
    import capstone.x86 as x86
    tracked, seen_imul = {dst}, False
    for w in insns[i + 1:i + 1 + _PREDICATE_WINDOW]:
        m, ops = w.mnemonic, w.operands
        if m.startswith(("j", "ret")) or m == "call":
            break
        regs = [_reg_family(w, o.reg) if o.type == x86.X86_OP_REG else None for o in ops]
        if m in ("and", "test") and len(ops) == 2 and ops[1].type == x86.X86_OP_IMM and ops[1].imm == 1 \
                and regs[0] in tracked and seen_imul:
            return True
        if m == "cmp" and len(ops) == 2 and ops[1].type == x86.X86_OP_IMM and ops[1].imm in (9, 10) \
                and regs[0] in tracked:
            return True
        if m == "imul" and any(r in tracked for r in regs if r):
            seen_imul = True
            if regs and regs[0]:
                tracked.add(regs[0])
            continue
        if not ops or ops[0].type != x86.X86_OP_REG:
            continue
        # x - 1 computed into a new register: `lea R, [T - 1]` (optimised builds)
        if m == "lea" and ops[1].type == x86.X86_OP_MEM and ops[1].mem.base and \
                _reg_family(w, ops[1].mem.base) in tracked:
            tracked.add(regs[0])
            continue
        if m in ("mov", "movsxd", "movzx", "movsx") and len(ops) == 2:
            if regs[1] in tracked:
                tracked.add(regs[0])                   # copy of the loaded value
            else:
                tracked.discard(regs[0])               # overwritten with something else
    return False


def find_opaque_globals(md, info: BinaryInfo, functions: list) -> list:
    """Globals that are never written, never have their address taken, and are only
    read into OLLVM opaque-predicate shapes (see `_feeds_opaque_predicate`).

    Ghidra later maps every returned address to read-only zero memory, so a false
    positive silently deletes real code; every filter here errs towards "not opaque".
    """
    import capstone.x86 as x86
    bss = [s for s in info.sections if s.nobits]
    if not bss:
        return []
    copy_ranges = _copy_reloc_ranges(info)

    def in_bss(a):
        return any(s.vaddr <= a < s.vaddr + s.size for s in bss)

    loads, stores, predicate_use, taken = Counter(), Counter(), Counter(), set()
    for _name, start, end in functions:
        code = info.read_va(start, end - start)
        insns = list(md.disasm(code, start))
        consts: dict = {}          # register family -> .bss address it holds (`mov R, imm`)
        for i, ins in enumerate(insns):
            ops = ins.operands
            if ins.mnemonic in ("mov", "movabs") and len(ops) == 2 and ops[0].type == x86.X86_OP_REG \
                    and ops[1].type == x86.X86_OP_IMM:
                consts[_reg_family(ins, ops[0].reg)] = ops[1].imm
                continue
            # an address held in a register that is used as a *value* (call argument,
            # arithmetic, stored to memory) escapes: the global may be written through it
            if ins.mnemonic == "call":
                taken.update(a for r, a in consts.items() if r in _ARG_REGS and in_bss(a))
            write_only_dst = ins.mnemonic in ("mov", "movabs", "movzx", "movsx", "movsxd", "lea")
            for k, op in enumerate(ops):
                if k == 0 and write_only_dst:
                    continue                             # destination is overwritten, not read
                if op.type == x86.X86_OP_REG and _reg_family(ins, op.reg) in consts \
                        and in_bss(consts[_reg_family(ins, op.reg)]):
                    taken.add(consts[_reg_family(ins, op.reg)])
                elif op.type == x86.X86_OP_IMM and in_bss(op.imm):
                    taken.add(op.imm)                    # push imm / mov [mem], imm
            if ins.mnemonic == "lea" and len(ops) == 2 and ops[1].type == x86.X86_OP_MEM:
                m = ops[1].mem
                a = ins.address + ins.size + m.disp if m.base == x86.X86_REG_RIP else \
                    m.disp if m.base == 0 and m.index == 0 else None
                if a is not None and in_bss(a):
                    taken.add(a)                         # &global
            for j, op in enumerate(ops):
                if op.type != x86.X86_OP_MEM or ins.mnemonic == "lea":
                    continue
                if op.mem.base == x86.X86_REG_RIP:
                    a = ins.address + ins.size + op.mem.disp
                elif op.mem.base == 0 and op.mem.index == 0:
                    a = op.mem.disp
                elif op.mem.index == 0 and _reg_family(ins, op.mem.base) in consts:
                    a = consts[_reg_family(ins, op.mem.base)] + op.mem.disp
                else:
                    continue
                if not in_bss(a):
                    continue
                is_store = j == 0 and len(ops) == 2 and ins.mnemonic not in ("cmp", "test")
                if is_store:
                    stores[a] += 1
                    continue
                loads[a] += 1
                if ins.mnemonic == "cmp" and len(ops) == 2 and ops[1].type == x86.X86_OP_IMM \
                        and ops[1].imm in (9, 10):
                    predicate_use[a] += 1                # `cmp dword [y], 9|10`
                elif ins.mnemonic in ("mov", "movsxd") and ops[0].type == x86.X86_OP_REG and \
                        _feeds_opaque_predicate(insns, i, _reg_family(ins, ops[0].reg)):
                    predicate_use[a] += 1
            # a register redefined by anything else loses its constant
            _r, w = _regs_touched(ins)
            for reg in w:
                consts.pop(_reg_family(ins, reg), None)
    return sorted(a for a in loads
                  if stores[a] == 0 and predicate_use[a] > 0 and a not in taken
                  and not any(lo <= a < hi for lo, hi in copy_ranges))


# ============================================================================ driver
def list_functions(info: BinaryInfo, md) -> list:
    """[(name, start, end)] from symbols, else entry + direct call targets."""
    execs = info.exec_sections()

    def sec_end(a):
        for s in execs:
            if s.vaddr <= a < s.vaddr + s.size:
                return s.vaddr + s.size
        return None

    funcs = [(n, a, a + sz) for n, (a, sz) in info.functions.items() if sz > 0 and sec_end(a)]
    if funcs:
        return sorted(funcs, key=lambda f: f[1])
    starts = {info.entry}
    for s in execs:
        code = info.data[s.offset:s.offset + s.size]
        for ins in md.disasm(code, s.vaddr):
            if ins.mnemonic == "call":
                t = _branch_target(ins)
                if t is not None and sec_end(t):
                    starts.add(t)
    starts = sorted(a for a in starts if sec_end(a))
    out = []
    for i, a in enumerate(starts):
        nxt = starts[i + 1] if i + 1 < len(starts) else sec_end(a)
        out.append((f"sub_{a:x}", a, min(nxt, sec_end(a))))
    return out


_GPR_INDEX = {n: i for i, n in enumerate(("ax", "cx", "dx", "bx", "sp", "bp", "si", "di"))}


def _mov_reg_zero(reg_name: str) -> bytes | None:
    """Encoding of `mov <reg32>, 0` for the 32/64-bit GPR `reg_name` (None for 8/16-bit).

    Writing the 32-bit register also zeroes the upper half of the 64-bit one, so this
    is a valid replacement for both `mov eax, [g]` and `mov rax, [g]` when g == 0.
    """
    n = reg_name.lower()
    if n.startswith("r") and n[1:].rstrip("d").isdigit():          # r8..r15 / r8d..r15d
        idx = int(n[1:].rstrip("d"))
        return bytes([0x41, 0xB8 + idx - 8]) + b"\0\0\0\0" if 8 <= idx <= 15 else None
    if len(n) == 3 and n[0] in "er" and n[1:] in _GPR_INDEX:        # eax.. / rax..
        return bytes([0xB8 + _GPR_INDEX[n[1:]]]) + b"\0\0\0\0"
    return None


def unflatten_binary(in_path, out_path, patch_opaque_loads: bool = True) -> dict:
    """Patch every flattened function; write the result to out_path.

    With `patch_opaque_loads`, every `mov reg, [g]` of a BCF opaque global g (always
    0 at run time) becomes `mov reg32, 0` + NOPs. The opaque predicates then fold in
    *any* decompiler (IDA, Ghidra, ...), so the output binary is clean on its own;
    without it only the Ghidra script (read-only memory trick) removes BCF.
    """
    info = load_binary(in_path)
    md = capstone_for(info)
    report = {"input": str(in_path), "output": str(out_path), "supported": md is not None,
              "functions": [], "opaque_globals": [], "patches": 0}
    data = bytearray(info.data)
    if md is None:
        Path(out_path).write_bytes(data)
        report["error"] = f"architecture {info.arch} not supported"
        return report
    funcs = list_functions(info, md)
    emu = DispatcherEmulator(info)
    for name, start, end in funcs:
        try:
            rep, patches = unflatten_function(md, info, emu, name, start, end)
        except Exception as exc:  # never break the pipeline on one function
            rep, patches = {"name": name, "address": hex(start), "error": repr(exc)}, []
        if rep.get("flattened"):
            report["functions"].append(rep)
        for va, code in patches:
            off = info.va_to_offset(va)
            if off is None:
                continue
            data[off:off + len(code)] = code
            report["patches"] += 1
    opaque = find_opaque_globals(md, info, funcs)
    report["opaque_globals"] = [hex(a) for a in opaque]
    if patch_opaque_loads and opaque:
        # Re-scan the *patched* bytes: with -fla the predicate loads often sit in the
        # condition that the CFF patch just relocated, so their old addresses are gone.
        ok, skipped = _patch_opaque_loads(md, replace(info, data=bytes(data)), funcs, set(opaque), data)
        report["opaque_loads_patched"], report["opaque_loads_skipped"] = ok, skipped
    Path(out_path).write_bytes(bytes(data))
    return report


def _patch_opaque_loads(md, info: BinaryInfo, funcs: list, opaque: set, data: bytearray) -> tuple:
    """Rewrite `mov reg, [g]` (g opaque) in place as `mov reg32, 0` + NOPs.

    Disassembles linearly per function (the patched code is still contiguous) and
    resolves absolute and RIP-relative operands only. Returns (patched, skipped).
    """
    import capstone.x86 as x86
    ok = skipped = 0
    for _name, start, end in funcs:
        for ins in md.disasm(info.read_va(start, end - start), start):
            ops = ins.operands
            if ins.mnemonic != "mov" or len(ops) != 2 or ops[0].type != x86.X86_OP_REG \
                    or ops[1].type != x86.X86_OP_MEM:
                continue
            m = ops[1].mem
            a = ins.address + ins.size + m.disp if m.base == x86.X86_REG_RIP else \
                m.disp if m.base == 0 and m.index == 0 else None
            if a not in opaque:
                continue
            code, off = _mov_reg_zero(ins.reg_name(ops[0].reg)), info.va_to_offset(ins.address)
            if code is None or len(code) > ins.size or off is None:
                skipped += 1
                continue
            data[off:off + ins.size] = code + b"\x90" * (ins.size - len(code))
            ok += 1
    return ok, skipped


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    a = ap.parse_args()
    print(json.dumps(unflatten_binary(a.input, a.output), indent=2))
