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
* **`ld.so` và `libc.so.6` trong rootfs phải cùng một bản glibc.** Lệch phiên bản (vd. `ld.so`
  2.43 của host + `libc` 2.36) làm các test Qiling fail với `*** stack smashing detected ***`
  ngay trong `dlopen`: ID tunable của hai bản khác nhau nên `__tunable_get_val` ghi đè stack canary.
  Kiểm tra: `strings qiling_rootfs/x8664_linux_glibc236/lib64/ld-linux-x86-64.so.2 | grep 'release version'`.

* **FLOSS rất tốn RAM trên binary lớn.** Trên BinKit binutils `-O0` (OLLVM), một lần chạy FLOSS đã
  lên tới 54 GB và bị kernel OOM-kill, kéo theo cả phiên desktop/VS Code. FLOSS giờ chạy với giới hạn
  bộ nhớ `FLOSS_MAX_MEM_GB` (mặc định 6) và thời gian `FLOSS_TIMEOUT` (mặc định 600 giây); vượt giới
  hạn thì bỏ qua chuỗi của FLOSS, vẫn giữ chuỗi Qiling thu được lúc chạy. Khi chạy hàng loạt, nên chạy
  trong một systemd unit có `MemoryMax`, ví dụ
  `systemd-run --user --collect -p MemoryMax=36G bash -c '...'`.

### Cài đặt không có sudo / Docker

`setup.sh` cần `apt` (sudo) và Docker (để lấy rootfs). Trên máy không có hai thứ này, làm thủ công:

1. **Venv:** `python3.11 -m venv ~/venvs/co2full_preproc && ~/venvs/co2full_preproc/bin/pip install -r requirements.txt`
   (Python 3.11 từ pyenv cũng được). `unicorn` 2.1.4 + `qiling` 1.4.6 chạy tốt.
2. **JDK 21:** giải nén bản tarball (vd. Temurin `jdk-21*_linux_x64`) vào `tools/`, rồi thêm vào
   cuối `~/venvs/co2full_preproc/bin/activate`:
   ```bash
   export JAVA_HOME="<preprocessing>/tools/jdk-21..."
   export PATH="$JAVA_HOME/bin:$PATH"
   export GHIDRA_HOME="<preprocessing>/tools/ghidra_11.4.3_PUBLIC"
   ```
3. **Ghidra 11.4.3** và **Qiling rootfs**: như các bước tương ứng trong `setup.sh` (`wget` + `unzip`,
   `git clone --sparse`), không cần quyền root.
4. **Rootfs glibc 2.36 không dùng Docker:** tải `libc6_2.36-9+deb12u*_amd64.deb` và
   `libgcc-s1_12.2.0-14+deb12u1_amd64.deb` từ `deb.debian.org/debian/pool/main/`, giải nén bằng
   `dpkg-deb -x`, rồi copy 6 file (`libc.so.6 libdl.so.2 libm.so.6 libpthread.so.0 libgcc_s.so.1
   ld-linux-x86-64.so.2`) vào `qiling_rootfs/x8664_linux_glibc236/lib/x86_64-linux-gnu/` và
   `ld-linux-x86-64.so.2` vào `.../lib64/`. **Lấy file thật trong `lib/x86_64-linux-gnu/` của gói,
   không `cp -L` symlink `lib64/ld-linux-x86-64.so.2`**: symlink đó là đường dẫn tuyệt đối nên
   `cp -L` sẽ copy `ld.so` của chính máy host (xem ghi chú ở trên).
5. Mẫu test trong `tests/bin/` đã build sẵn; chỉ cần Docker khi muốn build lại (`tests/build_samples.sh`).

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
| `deobfuscated.bin` | binary đã patch bỏ dispatcher CFF và các lệnh đọc biến opaque BCF (đầu vào của Ghidra, hoặc của IDA) |
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

**BCF.** Biến global opaque được xử lý ở hai chỗ:

1. **Trong binary** (`unflatten_binary(..., patch_opaque_loads=True)`, mặc định bật): mọi lệnh
   `mov reg, [g]` đọc một biến opaque `g` (luôn bằng 0 lúc chạy) được viết lại thành `mov reg32, 0`
   + `nop`. Bước này quét lại binary *sau* khi đã patch CFF, vì với `-fla -bcf` các lệnh đọc nằm trong
   điều kiện vừa được chép sang chỗ khác. Kết quả là `deobfuscated.bin` sạch với **mọi** decompiler
   (IDA, Ghidra...). Trên BinKit `elfedit -bcf -O0`: 816 lệnh được patch, Ghidra không dùng mẹo dưới đây
   vẫn không còn opaque predicate nào (283 → 0); `elfedit -all`: 780 lệnh, 0 bị bỏ qua. Hành vi chương
   trình không đổi (cùng mã thoát, stdout, stderr, file kết quả trên 7 bộ tham số).
2. **Trong Ghidra**: biến opaque được chuyển thành block memory read-only khởi tạo 0, nên decompiler
   tự fold opaque predicate và xoá nhánh giả (vẫn giữ, để xử lý cả các lệnh đọc không patch được). Vì một global bị nhận nhầm sẽ làm Ghidra
**xoá code thật một cách im lặng**, `find_opaque_globals` chỉ nhận một địa chỉ trong `.bss` khi
thoả *tất cả*:

* không có lệnh nào của chương trình ghi vào nó;
* địa chỉ của nó không bị lấy ra làm giá trị (`lea`, immediate, thanh ghi chứa địa chỉ được truyền
  làm tham số `call`/dùng trong phép tính) — vd. `fread(&elf_header, ...)` ghi gián tiếp;
* không nằm trong vùng `R_*_COPY` (biến của libc như `stdout`, `stderr`, `optarg`, do libc ghi);
* giá trị vừa đọc vào thanh ghi (hoặc bản copy của thanh ghi đó) thực sự đi vào đúng dạng
  `x*(x-1)&1` (`imul` rồi `and`/`test` với 1) hoặc `y<10` (`cmp` với 9/10).

Bản trước chỉ cần "có `imul` hoặc `cmp ..., 0xa` trong 12 lệnh sau khi đọc", nên trên BinKit
`elfedit` đã fold `elf_header`, `stdout`, `stderr`, `optarg`, `_xexit_cleanup` thành 0: `get_file_header`
còn 14/111 dòng và luôn báo lỗi, `fprintf(stderr, ...)` thành `fprintf(NULL, ...)`. Trên 20 binary
BinKit `-O0` (`bcf`, `all`) bộ lọc mới không còn nhận nhầm global nào và vẫn tìm đủ các biến
`x`/`y` được dùng (vd. 66/70 ở `elfedit`; 4 biến còn lại không được tham chiếu).

**Danh sách hàm trên binary đã strip.** Co2FuLL làm việc trên binary strip. `binutil.load_binary`
lấy hàm từ symbol *và* từ các FDE trong `.eh_frame` (strip không xoá section này; mỗi FDE cho
đúng địa chỉ + kích thước một hàm, bỏ vùng `.plt*`). Trước đây chỉ dùng symbol: một binary strip vẫn
export vài hàm qua `.dynsym` (BinKit `elfedit`: `error`, `warn`) nên detect/unflattener chỉ thấy 2
hàm → không có tín hiệu CFF/BCF nào, stage 0 bypass binary bị obfuscate. Sau khi sửa, `elfedit -all`
đã strip cho kết quả như bản còn symbol (42 hàm flatten, 39 gỡ hết, 68 opaque global).

**Tham số hàm (Ghidra).** OLLVM giữ nguyên DWARF gốc trong khi viết lại code, nên vị trí tham số
Ghidra lấy từ DWARF có thể sai: hàm bị gắn *custom storage* với calling convention `unknown` (BinKit
`elfedit -bcf`: 15 hàm, vd. `usage(stream=RAX, exit_status=ECX)` thay vì `RDI/ESI`). Khi đó mọi lời
gọi tới hàm đó bị decompile với tham số sai (`usage((FILE *)0x0,0)` thay cho `usage(stderr,1)`).
Script Ghidra đặt lại calling convention mặc định cho các hàm này trước khi decompile (giữ tên/kiểu
tham số); số hàm được sửa ghi ở `stage0_report.json → ghidra.param_storage_reset`. Bước này chạy
cả khi xuất pseudocode "trước xử lý" (`--no-unflatten`) vì đây là lỗi của decompiler, không phải
của obfuscation.

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
  vẫn chạy và xuất pseudocode gốc. Trên BinKit `elfedit` `-O2`: detector báo `cff_pattern` cho 26
  hàm nhưng unflattener không gỡ được hàm nào — state nằm trong thanh ghi (`ebx`, `r11d`, ...),
  dispatcher là cây `jle/jg`, và ~2/3 cạnh quay về dispatcher gán state bằng một thanh ghi khác
  (`mov ebx, ecx`) mà giá trị được chọn bằng `cmov` từ đầu hàm (điều kiện `if` thật bị LICM kéo
  lên prologue). Hỗ trợ `-O2` cần phân tích data-flow (hoặc làm ở mức P-code/SSA của Ghidra),
  không chỉ đổi stack slot thành thanh ghi.
* Một số hàm `fla` còn 1 khối không giải được (`unresolved_blocks` trong report; BinKit `elfedit`
  `-O0`: 1/42 hàm ở `fla`, 3/42 ở `all`).
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

`test_cff.py::test_opaque_globals_exclude_real_globals_binkit` là regression test cho lỗi BCF ở trên:
chạy trên `Data_advance/selected_10_O0/bcf/binutils-2.30_clang-obfus-bcf_x86_64_O0_elfedit.elf`
(không nằm trong repo; test tự skip nếu thiếu file) và kiểm tra mọi opaque global đều là biến
`x`/`y` của OLLVM. `test_stripped_binary_still_unflattened` strip bản `all` của cùng chương trình
và kiểm tra detect + unflattener vẫn thấy đủ hàm.

Kết quả của lần chạy test được công bố trong [`output/evaluation/`](output/evaluation/)
(bảng tổng hợp: [`evaluation.md`](output/evaluation/evaluation.md); mỗi mẫu có `stage0_report.json`,
`recovered_*.json`, `clean_pseudocode/`, `deobfuscated.bin`). Các output khác trong `output/`
bị git-ignore. Tạo lại: `python evaluate.py` (đường dẫn trong JSON được ghi dạng tương đối).

## Đánh giá trên BinKit (binutils-2.30 `elfedit`, x86-64 `-O0`)

Dữ liệu: `Data_advance/selected_10_O0/` — binary build sẵn của BinKit (Obfus dataset, Obfuscator-LLVM
4.0.1; bản clean từ Normal dataset, clang 4.0.0, còn DWARF/symbol). Mỗi biến thể: *trước* = Ghidra
xuất pseudocode không deobfuscate; *sau* = `run_stage0(..., force=True)`. 48 hàm (bỏ CRT/thunk) được
ghép theo tên với bản clean. "Độ giống" = tỉ lệ khớp chuỗi token (difflib) sau khi chuẩn hoá tên tự
sinh của Ghidra (`local_*`, `uVar*`, `DAT_*`, hằng số); tên hàm gọi, chuỗi, toán tử giữ nguyên.

| Biến thể | Số dòng ×clean | `while(true)` ×clean | Hằng state CFF ×clean | Tham chiếu `x`/`y` | Độ giống TB | Hàm ≥ 0.8 |
|---|---|---|---|---|---|---|
| sub | 1.01 → 1.01 | 1.00 → 1.00 | 1.13 → 1.13 | 0 → 0 | 0.978 → 0.978 | 96% → 96% |
| bcf | 1.76 → 1.12 | 2.50 → 1.00 | 4.94 → 1.00 | 839 → 0 | 0.649 → 0.881 | 27% → 75% |
| fla | 2.54 → 1.13 | 60.0 → 1.50 | 23.3 → 1.29 | 0 → 0 | 0.498 → 0.895 | 12% → 83% |
| all | 5.56 → 1.37 | 95.8 → 1.50 | 52.6 → 0.87 | 1523 → 0 | 0.315 → 0.787 | 12% → 60% |

* `sub`: pipeline không có bước riêng; decompiler của Ghidra đã tự rút gọn gần hết ở `-O0`.
* `fla`: 42 hàm bị flatten được phát hiện, 41 gỡ hoàn toàn (673 patch).
* Độ giống token là heuristic: không chứng minh tương đương ngữ nghĩa và không bắt được lỗi
  sai tham số/hằng số — hai lỗi ở mục "Cách deobfuscate hoạt động" (BCF fold nhầm global, tham số
  hàm sai) đều được tìm ra bằng cách đọc pseudocode, không phải từ con số này.
* Cùng chương trình ở `-O2` (đo *trước* khi sửa hai lỗi trên, chưa chạy lại): `bcf` 0.678 → 0.868,
  còn `fla`/`all` gần như không đổi (0.43 → 0.43, 0.29 → 0.32) do giới hạn unflattener ở trên.
