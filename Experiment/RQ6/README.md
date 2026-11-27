# RQ6 — Stage 0 có làm thay đổi kết quả của Co²FuLL trên binary clean không?

> **RQ6.** Bước detect của stage 0 có nhận ra đúng binary clean để bỏ qua không? Và nếu detect nhận
> nhầm (mô phỏng bằng `--force`), stage 0 có làm thay đổi đầu vào, và do đó kết quả, của Co²FuLL không?

| | Tập | Nội dung |
|---|---|---|
| **Base** | B | Binary clean (BinKit) → Co²FuLL |
| **So sánh** | D | Tập B → stage 0 (`--force`) → Co²FuLL |

**Lập luận:** RQ1–RQ4 được làm trên binary clean (dữ liệu cũ). Muốn đưa stage 0 vào pipeline mà
không ảnh hưởng tới các kết quả đó, cần chứng minh hai điều:

1. **Detect hoạt động tốt:** binary clean bị bỏ qua, nên D giống B và Co²FuLL nhận đúng đầu vào cũ.
2. **Kể cả khi detect nhận nhầm, stage 0 cũng không làm hỏng:** D (ép chạy) vẫn giống, hoặc gần
   giống, B.

Không cần tập ứng viên riêng: nếu đầu vào của Co²FuLL không đổi thì kết quả không đổi. Chỉ khi đầu vào
thật sự khác (mục 3, phần 2b) mới phải chạy pipeline để đo mức chênh lệch.

Trạng thái: **phần 1 và 2a đã có kết quả** (từ `Data_RQ5_RQ6/summary.csv` và `cmp`):

* Detect nhận nhầm **0/10** binary clean.
* Khi ép chạy, **10/10 binary D giống hệt B từng byte**: stage 0 không tìm thấy hàm flatten hay biến
  opaque nào để patch.
* Kết luận: nếu không đưa `recovered_strings.json` vào context, kết quả Co²FuLL trên D trùng hoàn toàn
  với B, nên không cần chạy IDA/LLM cho RQ6. Phần 2b chỉ cần nếu nhóm bổ sung chuỗi khôi phục vào
  context (14 chuỗi cho cả 10 binary). Phần 4 (detect trên dữ liệu cũ, cỡ mẫu lớn) chưa chạy.

---

## 1. Dữ liệu đầu vào

Tất cả nằm trong [`Data_RQ5_RQ6/`](../../Data_RQ5_RQ6/README.md).

| Đường dẫn | Nội dung |
|---|---|
| `Data_RQ5_RQ6/B/*.elf.strip` | 10 binary clean (BinKit, clang 4.0.0, x86-64, `-O0`), đã strip |
| `Data_RQ5_RQ6/D/*.elf.strip` | Cùng 10 binary sau stage 0 `--force`. Cùng tên file, cùng địa chỉ hàm với B |
| `Data_RQ5_RQ6/D/stage0/<bin>/stage0_report.json` | `detection.is_obfuscated` + `detection.signals`: kết quả detect **trước khi** bị ép; `deobfuscation.unflatten`: số hàm flatten, số biến opaque, số patch |
| `Data_RQ5_RQ6/D/stage0/<bin>/recovered_imports.json`, `recovered_strings.json` | Import/chuỗi stage 0 khôi phục được (chỉ ảnh hưởng nếu được đưa vào context) |
| `Data_RQ5_RQ6/summary.csv` | Một dòng cho mỗi binary C/D, gồm `detected_without_force`, `signals`, `flattened_funcs`, `opaque_globals`, `opaque_loads_patched`, `seconds` |

## 2. Chỉ số đo

| Phần | Chỉ số | Lấy từ đâu | Kỳ vọng |
|---|---|---|---|
| **1. Detect** | **Tỉ lệ nhận nhầm** trên binary clean = số binary B có `detected_without_force = True` / 10 | `summary.csv` (dòng D) | 0/10 |
| | (tham khảo) Tỉ lệ phát hiện đúng trên binary obfuscate, theo từng loại | `summary.csv` (dòng C) | `bcf`/`fla`/`all`: 10/10; `sub`: xem mục 4 |
| **2a. Khi ép chạy** | Số binary D khác B về byte; số hàm bị patch (`flattened_funcs`), số lệnh đọc opaque bị patch | `cmp`, `summary.csv` | 0 |
| | Số import/chuỗi khôi phục thêm so với import/chuỗi tĩnh | `recovered_*.json`, `stage0_report.json` | Báo cáo, không đặt ngưỡng |
| | Thời gian stage 0 thêm vào mỗi binary | `summary.csv` (`seconds`) | Báo cáo |
| **2b. Chỉ khi D ≠ B** (byte, hoặc context nếu nhóm bổ sung import/chuỗi) | Trên đúng các hàm bị thay đổi: ΔRecall@5, ΔF2, tỉ lệ cặp LLM trả lời giống nhau | Chạy pipeline như RQ5 (mục 3 của [`../RQ5/README.md`](../RQ5/README.md)), truy vấn lấy từ B / D | \|ΔF2\| ≤ 2 điểm phần trăm (chốt trước khi chạy) |

## 3. Luồng chạy

```bash
# Phần 1 + 2a: không cần IDA, chạy được ngay sau khi dựng xong Data_RQ5_RQ6
cd Data_RQ5_RQ6
# (a) detect nhận nhầm?
python3 -c "import csv; r=[x for x in csv.DictReader(open('summary.csv')) if x['set']=='D']; \
print(sum(x['detected_without_force']=='True' for x in r), '/', len(r), 'clean binaries flagged')"
# (b) ép chạy có đổi byte nào không?
for f in B/*.strip; do cmp -s "$f" "D/$(basename "$f")" && echo "same  $f" || echo "DIFF  $f"; done
```

* Nếu (a) = 0/10 và (b) toàn `same`: **D giống hệt B**. Embedding, pseudocode và context từ IDA của D
  trùng hoàn toàn với B, nên kết quả Co²FuLL không đổi, kể cả với dữ liệu cũ của RQ1–RQ4. Kết luận
  được rút ra trực tiếp từ dữ liệu, không cần chạy IDA hay LLM cho RQ6.
* Nếu có binary `DIFF`, hoặc nhóm quyết định bổ sung import/chuỗi của stage 0 vào context (bước 3 trong
  RQ5): chạy phần 2b trên đúng các binary/hàm bị ảnh hưởng.

## 4. Mở rộng nên làm: kiểm tra detect trên nhiều binary clean hơn

10 binary là cỡ mẫu nhỏ cho một tỉ lệ nhận nhầm. Detect chạy nhanh (vài giây mỗi binary) và không cần
IDA, nên có thể chạy trên **dữ liệu cũ** đã có sẵn: `DBs/Binkit-1.0-normal-strip-binaries/` (binary
clean BinKit đã strip, nhiều kiến trúc và mức tối ưu).

```bash
source ~/venvs/co2full_preproc/bin/activate
cd preprocessing
python -c "
import sys, glob, collections
from detect import analyze_signals
c = collections.Counter()
for p in glob.glob('../DBs/Binkit-1.0-normal-strip-binaries/*/*x86_64*.strip'):
    s = analyze_signals(p); c[s['is_obfuscated']] += 1
    if s['is_obfuscated']: print(p, [k for k, v in s['signals'].items() if v])
print(c)"
```

Nên báo cáo tỉ lệ nhận nhầm **theo từng mức tối ưu** (`O0`–`O3`) và từng tín hiệu. Lưu ý: phần quét mã
(`cff_pattern`, `bcf_pattern`) chỉ hỗ trợ x86/x86-64; với ARM/MIPS chỉ có các tín hiệu entropy, import và chuỗi.

## 5. Điều cần lưu ý

* `--force` chỉ để **mô phỏng** detect nhận nhầm. Khi chạy thực tế, binary bị coi là clean được bỏ
  qua hoàn toàn: stage 0 chỉ copy nguyên file, không sinh ra gì khác.
* Ở trường hợp lý tưởng (D giống hệt B), kết luận "không ảnh hưởng" là **chính xác**, không phải
  ước lượng thống kê. Đó là lý do RQ6 không cần chạy pipeline cho mọi binary.
* Chỉ `-O0`, x86-64 cho phần 1–2; phần 4 mở rộng ra mọi kiến trúc và mức tối ưu có trong dữ liệu cũ.
