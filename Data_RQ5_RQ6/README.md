# Dữ liệu cho RQ5 và RQ6

Bốn tập binary dùng cho hai thí nghiệm mở rộng. Thiết kế thí nghiệm, luồng chạy và chỉ số đo xem ở
[`Experiment/RQ5/README.md`](../Experiment/RQ5/README.md) và [`Experiment/RQ6/README.md`](../Experiment/RQ6/README.md).

| Tập | Nội dung | Dùng cho |
|---|---|---|
| **A** | Binary obfuscate (`sub`, `bcf`, `fla`, `all`), đã strip | RQ5 base |
| **B** | Binary clean, đã strip | RQ6 base; tập ứng viên của RQ5 |
| **C** | A sau stage 0 (`--force`) | RQ5 so sánh |
| **D** | B sau stage 0 (`--force`) | RQ6 so sánh |

**Chưa có pseudocode.** Nhóm sẽ dùng IDA Pro để xuất pseudocode, embedding và context cho cả 4 tập.

## 1. Nguồn gốc

* Lấy từ `Data_advance/selected_10_O0/`: binary build sẵn của **BinKit**, x86-64, `-O0`, còn symbol và DWARF.
  * Obfuscate: Obfus dataset, Obfuscator-LLVM 4.0.1 (`clang-obfus-{sub,bcf,fla,all}`).
  * Clean: Normal dataset, clang 4.0.0.
* 10 chương trình: a2ps-4.14 (`a2ps`, `fixnt`); binutils-2.30 (`addr2line`, `ar`, `as`, `c++filt`,
  `elfedit`, `gprof`, `nm`, `objcopy`).
* Strip bằng `strip --strip-all` (giống bối cảnh BinKit `*-strip` mà Co²FuLL dùng). Tên file theo quy ước
  BinKit/Co²FuLL: `<package>_<compiler>_x86_64_O0_<program>.elf.strip`.

## 2. Cấu trúc thư mục

```
Data_RQ5_RQ6/
├── A/{sub,bcf,fla,all}/<bin>.elf.strip          # 40 binary obfuscate
├── B/<bin>.elf.strip                            # 10 binary clean
├── C/{sub,bcf,fla,all}/<bin>.elf.strip          # A sau stage 0, CÙNG TÊN FILE với A
│   └── <variant>/stage0/<bin>/
│       ├── stage0_report.json                   # detect, unpack, chuỗi, kết quả gỡ CFF/BCF từng hàm
│       ├── recovered_imports.json               # {"0x<addr>": "<api>"} (rỗng với bộ này)
│       ├── recovered_strings.json               # chuỗi FLOSS + chuỗi lúc chạy (Qiling)
│       └── log.txt
├── D/<bin>.elf.strip  +  D/stage0/<bin>/...     # B sau stage 0, cùng cấu trúc với C
├── ground_truth/{clean,sub,bcf,fla,all}/<bin>.json   # {"0x<addr>": {"name", "size"}}
├── summary.csv                                  # một dòng cho mỗi binary C/D (bảng ở mục 4)
├── build_sets.py                                # script dựng toàn bộ thư mục này
└── build.log, build_part1.log                   # log các lần chạy
```

* **Địa chỉ hàm không đổi giữa A↔C và B↔D**: stage 0 patch binary tại chỗ (không có binary nào bị
  pack, nên không có bước unpack làm dời địa chỉ). Vì vậy `ground_truth/<variant>/` dùng chung cho cả
  A và C, `ground_truth/clean/` dùng chung cho cả B và D.
* Ground truth lấy từ bảng symbol của binary **chưa strip**: mọi `STT_FUNC` có địa chỉ.
* Dung lượng: A 141 MB, B 13 MB, C 152 MB, D 13 MB, ground truth 5,7 MB; tổng 323 MB.

## 3. Stage 0 đã làm gì với C và D

`build_sets.py` chạy `run_stage0(..., force=True, skip_ghidra=True)` rồi `unflatten_binary(...)`:

| Bước | Việc | Ảnh hưởng tới file `.elf.strip` của C/D |
|---|---|---|
| 0.1 | Detect (entropy, import, mật độ chuỗi, mẫu CFF, mẫu BCF, chữ ký packer) | Không. Kết quả ghi ở `detection` trong báo cáo; `--force` ép chạy tiếp dù detect nói clean |
| 0.2a | Unpack (UPX → Qiling) | Không: không binary nào bị pack (`unpack = none`) |
| 0.2b | Khôi phục import và chuỗi (FLOSS + Qiling) | Không. Chỉ ghi `recovered_*.json` (để bổ sung context nếu nhóm muốn) |
| 0.2c | Gỡ CFF (patch nhảy thẳng tới khối thật) + **patch lệnh đọc biến opaque BCF thành hằng 0** | **Có**: đây là phần làm binary sạch, để IDA (hay decompiler bất kỳ) tự rút gọn |

Không chạy Ghidra, và không xuất pseudocode.

## 4. Số liệu

Tổng hợp từ `summary.csv` (mỗi dòng 10 binary):

| Biến thể | Detect là obfuscate (khi chưa ép) | Tín hiệu | Hàm flatten tìm thấy | Gỡ hoàn toàn | Biến opaque | Lệnh đọc opaque đã patch | Binary bị đổi byte | Thời gian/binary (min / trung vị / max) |
|---|---|---|---|---|---|---|---|---|
| clean (→ D) | **0/10** | — | 0 | — | 0 | 0 | **0/10** | 8 / 621 / 630 s |
| sub | **0/10** | — | 0 | — | 0 | 0 | **0/10** | 8 / 626 / 630 s |
| bcf | 10/10 | `bcf_pattern` 10, `low_strings` 9 | 0 | — | 8.242 | 432.128 | 10/10 | 9 / 679 / 704 s |
| fla | 10/10 | `cff_pattern` 10, `low_strings` 9 | 12.985 | 11.087 (85,4%) | 0 | 0 | 10/10 | 12 / 492 / 661 s |
| all | 10/10 | `cff_pattern` 10, `bcf_pattern` 10, `low_strings` 9 | 14.425 | 11.882 (82,4%) | 8.272 | 441.100 | 10/10 | 18 / 1.070 / 1.264 s |

**Rút ra được ngay (chưa cần IDA):**

* **RQ6, phần 1 và 2a:** detect **không nhận nhầm** binary clean nào (0/10). Khi ép chạy, stage 0 **không
  đổi một byte nào** của 10 binary clean (`cmp B/x D/x` đều giống nhau). Vậy embedding, pseudocode và
  context từ IDA của D trùng hoàn toàn với B. Chỉ còn khác ở `recovered_strings.json` (14 chuỗi cho cả
  10 binary), và chỉ có tác dụng nếu nhóm đưa chúng vào context.
* **`sub` không được phát hiện và không được xử lý:** 0/10 bị detect, và C/sub giống hệt A/sub từng byte.
  Stage 0 chưa có bước xử lý instruction substitution. Ở RQ5, kết quả `sub` của C sẽ trùng với A (trừ
  phần context bổ sung).
* Khoảng 15–18% số hàm flatten còn ít nhất một khối chưa gỡ được (`unresolved_blocks` trong báo cáo):
  các hàm này chỉ được làm sạch một phần.
* Không binary nào có import bị giấu (`recovered_apis = 0`), điều này đúng với OLLVM (OLLVM không giấu import).

## 5. Lưu ý về chuỗi khôi phục (`recovered_strings.json`)

* **FLOSS hết thời gian (600 giây) ở phần lớn binary lớn.** Số binary có 0 chuỗi FLOSS: clean 8/10,
  sub 9/10, bcf 10/10, fla 0/10, all 2/10. Thời gian khoảng 620–630 giây ở clean/sub chính là FLOSS chạy
  hết thời gian. Ở các binary này, `recovered_strings.json` chỉ có chuỗi Qiling thu được lúc chạy.
* FLOSS bị giới hạn 6 GB RAM (`FLOSS_MAX_MEM_GB`). Không có giới hạn này, một lần chạy FLOSS đã lên
  54 GB và làm sập cả phiên desktop.
* Muốn chuỗi đầy đủ hơn: tăng `FLOSS_TIMEOUT` rồi chạy lại riêng bước 0.2b. Việc này không ảnh hưởng tới
  các file binary đã làm sạch.

## 6. Dựng lại

```bash
source ~/venvs/co2full_preproc/bin/activate
# chạy trong một systemd unit có MemoryMax để một tiến trình ngốn RAM không kéo sập cả phiên desktop
systemd-run --user --collect --unit=rq56-build -p MemoryMax=36G -p WorkingDirectory=$PWD \
  bash -c 'source ~/venvs/co2full_preproc/bin/activate; python Data_RQ5_RQ6/build_sets.py --jobs 4 > Data_RQ5_RQ6/build.log 2>&1'
```

Script bỏ qua các binary đã có `stage0_report.json`. Muốn làm lại một binary thì xoá thư mục
`stage0/<bin>/` của nó. Với 4 luồng, toàn bộ mất khoảng 2–3 giờ (bản `all` của các binary binutils lớn
mất khoảng 18–21 phút mỗi binary).
