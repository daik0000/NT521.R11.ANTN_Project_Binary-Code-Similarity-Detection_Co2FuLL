# Stage 0 — Binary Normalization Pre-processing cho Co2FuLL

Hiện thực của `../preprocessing_pipeline_design.md`. Không sửa file nào của Co2FuLL gốc.

```
detect.py            0.1  Obfuscation signal check (entropy, imports, strings, CFF, BCF, packer)
unpack.py            0.2a UPX -d  →  fallback Qiling OEP + memory dump
recover_imports.py   0.2b FLOSS + Qiling run-time string scan, dlsym/GetProcAddress hooks
cff_unflatten.py     0.2c pre-pass: gỡ OLLVM control-flow flattening, tìm biến opaque của BCF
deobfuscate_cfg.py   0.2c Ghidra headless wrapper
run_pipeline.py      entry point (CLI)
inject_context.py    §6.1 merge imports/strings vào features của Co2FuLL
inject_pseudocode.py §6.2 ưu tiên pseudocode đã deobfuscate cho LLM
evaluate.py          tự điền bảng tiêu chí §8.3
config.py            đường dẫn Ghidra/rootfs, ngưỡng detection
ghidra_scripts/deobfuscate_headless.py   Jython: BCF read-only, label import, export pseudocode
qiling_scripts/dump_unpacked.py          OEP detection + dump
qiling_scripts/hook_imports.py           hook dlopen/dlsym, LoadLibrary/GetProcAddress
tests/                                   pytest + mẫu C + script build mẫu OLLVM
```

## Cài đặt (Ubuntu/WSL)

```bash
bash setup.sh                       # apt + venv Python 3.11 + Ghidra 11.4.3 + Qiling rootfs
source ~/venvs/co2full_preproc/bin/activate
bash tests/build_samples.sh         # build mẫu test bằng Docker image icyguider/ollvm
```

Ghi chú môi trường:
* **Python 3.11** — `qiling`/`flare-floss` pin `pillow` cũ, không build được trên 3.13+.
* **JDK 21** — Ghidra 11.2+ yêu cầu Java 21 (bản thiết kế ghi 17).
* **Rootfs glibc 2.36** — rootfs gốc của Qiling dùng glibc cũ, không load được binary cần
  `GLIBC_2.34+` (crash ngay trong ld.so). `setup.sh` tạo `qiling_rootfs/x8664_linux_glibc236`
  từ `debian:12-slim`; `config.default_rootfs()` tự ưu tiên rootfs này.

## Chạy

```bash
python run_pipeline.py sample.bin                       # tự detect, bypass nếu clean
python run_pipeline.py sample.bin --force --output-dir ./output
python run_pipeline.py sample.bin --skip-ghidra --no-floss   # nhanh, chỉ 0.1–0.2b
python evaluate.py                                      # chạy toàn bộ mẫu, ghi output/evaluation/evaluation.md
```

Output `output/<binary>/`:

| File | Nội dung |
|---|---|
| `normalized.bin` | binary sau unpack (hoặc bản copy nếu không packed) |
| `recovered_imports.json` | `{"0x4040a0": "puts", ...}` — địa chỉ link-time của **slot con trỏ** và **call site** |
| `recovered_strings.json` | string FLOSS + string chỉ xuất hiện lúc chạy |
| `deobfuscated.bin` | binary đã patch bỏ dispatcher CFF (đầu vào của Ghidra) |
| `clean_pseudocode/0x%08x.c` | pseudocode mỗi hàm (địa chỉ link-time, khớp IDA) + `index.json` (tên, calls) |
| `stage0_report.json` | toàn bộ signal, phương thức unpack, thống kê unflatten, lỗi nếu có |

## Cách deobfuscate hoạt động

**Unpack (Qiling).** Theo dõi các page của image bị ghi; block đầu tiên chạy trên page vừa ghi
(đi vào từ code chưa bị ghi) là ứng viên OEP. Nếu unpacker đã khôi phục ELF header gốc trong
memory thì OEP = `e_entry` của header đó (bỏ qua các stub phụ như bộ de-filter của UPX), và image
được snapshot *trước* khi ld.so áp relocation → bản dump trùng byte-by-byte với bản gốc trong mọi
`PT_LOAD`.

**CFF (`cff_unflatten.py`).** Mỗi hàm: dựng CFG (capstone) → biến state = stack slot được gán nhiều
hằng 32-bit ngẫu nhiên nhất → dispatcher = khối có nhiều predecessor nhất + các khối chỉ
load/so sánh state → với mỗi hằng state, emulate dispatcher bằng unicorn để tìm khối đích thật →
patch:

```
mov [S], C ; jmp loopEnd                               →  jmp succ(C)
mov R,A ; mov R2,B ; cmp.. ; cmovCC R,R2 ; mov [S],R ; jmp   →  cmp.. ; jCC succ(B) ; jmp succ(A)
```

**BCF.** Biến global chỉ được đọc, không bao giờ bị ghi, và đi vào biểu thức `x*(x-1)&1` / `y<10`
được chuyển (trong Ghidra) thành block memory read-only khởi tạo 0 → decompiler tự fold opaque
predicate và xoá nhánh giả.

## Khác biệt so với bản thiết kế

| Thiết kế | Hiện thực | Lý do |
|---|---|---|
| `-noanalysis` + `analyzeAll()`, cờ `-analyzeHeadless` | auto-analysis mặc định của headless | `-analyzeHeadless` không phải cờ hợp lệ |
| Script Ghidra dùng f-string | Jython 2.7 | Ghidra chạy `.py` bằng Jython 2.7 |
| `OllvmDeflat.py` (FFRI/ghidra-deobfuscator) | pre-pass riêng `cff_unflatten.py` (hướng 2 trong ghi chú §5.4) | không dùng được script ngoài; pre-pass kiểm thử được độc lập |
| `ql.run()` trên binary tại chỗ | copy vào `rootfs/tmp/` | stub UPX mở `/proc/self/exe`, Qiling yêu cầu file nằm trong rootfs |
| Docker `obfuscator-llvm/obfuscator` | `icyguider/ollvm` (heroims/obfuscator, LLVM 13) | image trong tài liệu không tồn tại trên Docker Hub |
| `test_subject.c`: `return tmp[0]` sau `free` | lưu kết quả trước `free` | use-after-free |
| Thêm signal `bcf_pattern`, `packer_signature` | — | giảm false negative |

## Giới hạn

* Unflattener nhắm OLLVM build `-O0` (state nằm trên stack, x86/x86-64). Build `-O2` (state
  trong thanh ghi), dispatcher dạng jump table, ARM/MIPS → báo `unsupported`/không patch, pipeline
  vẫn chạy và xuất pseudocode gốc.
* `-sub` (instruction substitution) chỉ được Ghidra tự rút gọn một phần (vd. `n + 1` vẫn hiện
  là `-(-1 - n)`), và các biến stack mà `fla` tạo ra (reg2mem) vẫn còn → pseudocode sau xử lý
  đúng cấu trúc/lời gọi nhưng dài hơn bản clean (duplicate_message: 35 dòng so với 10; bản thô 90).
* Ngoài phạm vi (theo §7): function fission/fusion, VM-based (VMProtect/Themida).
* Import recovery cần chương trình thực sự chạy tới đoạn resolve API (không có input/argv đặc biệt).
* Hook Windows (`GetProcAddress`) đã viết nhưng chưa kiểm thử: cần rootfs Windows chứa DLL thật.

## Test

```bash
cd tests
pytest -q -m "not ghidra and not slow"   # ~20 s: detect, unpack, recover, CFF (+ Qiling)
pytest -q -m "ghidra or slow" -s         # ~6–8 min: FLOSS + Ghidra end-to-end, in bảng §8.3
```
