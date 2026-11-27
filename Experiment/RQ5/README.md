# RQ5 — Pipeline mới xử lý binary bị obfuscate tốt đến đâu?

> **RQ5.** Khi thêm stage 0 (deobfuscate) vào trước Co²FuLL, khả năng tìm đúng hàm của Co²FuLL
> trên binary bị obfuscate thay đổi thế nào so với khi không có stage 0?

| | Tập | Nội dung |
|---|---|---|
| **Base** | A | Binary obfuscate (BinKit) → Co²FuLL |
| **So sánh** | C | Tập A → stage 0 (`--force`) → Co²FuLL |

**Kỳ vọng:** C tốt hơn A rõ rệt ở `fla`, `bcf`, `all`. Ở `sub`, C gần bằng A, vì stage 0 không có
bước xử lý riêng cho instruction substitution (xem mục 5).

Trạng thái: **dữ liệu đã sẵn sàng** (thống kê stage 0 ở [`Data_RQ5_RQ6/README.md`](../../Data_RQ5_RQ6/README.md), mục 4).
Các bước IDA, embedding và LLM chưa chạy.

---

## 1. Dữ liệu đầu vào

Tất cả nằm trong [`Data_RQ5_RQ6/`](../../Data_RQ5_RQ6/README.md). Cách dựng xem trong README của thư mục đó.

| Đường dẫn | Vai trò trong RQ5 |
|---|---|
| `Data_RQ5_RQ6/A/{sub,bcf,fla,all}/*.elf.strip` | Phía **truy vấn**, điều kiện base |
| `Data_RQ5_RQ6/C/{sub,bcf,fla,all}/*.elf.strip` | Phía **truy vấn**, điều kiện so sánh. **Cùng tên file, cùng địa chỉ hàm** với A |
| `Data_RQ5_RQ6/C/<variant>/stage0/<bin>/recovered_imports.json`, `recovered_strings.json` | Import và chuỗi stage 0 khôi phục được, dùng để bổ sung **context** cho C |
| `Data_RQ5_RQ6/B/*.elf.strip` | **Tập ứng viên** (pool) cho cả hai điều kiện: bản clean cùng chương trình |
| `Data_RQ5_RQ6/ground_truth/<variant>/<bin>.json` | `{"0x<addr>": {"name", "size"}}` lấy từ binary chưa strip → nhãn |

* 10 chương trình (a2ps: `a2ps`, `fixnt`; binutils-2.30: `addr2line`, `ar`, `as`, `c++filt`,
  `elfedit`, `gprof`, `nm`, `objcopy`), x86-64, `-O0`.
* Obfuscate bằng Obfuscator-LLVM 4.0.1 (`clang-obfus-{sub,bcf,fla,all}`). Clean bằng clang 4.0.0.
  Tất cả đều là binary build sẵn của BinKit.
* Stage 0 sửa binary **tại chỗ**, nên địa chỉ của một hàm ở C trùng với ở A. Vì vậy dùng chung
  file ground truth của A cho C.

**C khác A ở đâu:**
* `fla`, `all`: các hàm bị flatten đã được gỡ (patch nhảy thẳng tới khối thật).
* `bcf`, `all`: mọi lệnh đọc biến opaque (`x`, `y`) đã được đổi thành hằng 0. Nhờ vậy IDA tự rút
  gọn opaque predicate và bỏ nhánh giả.
* `sub`: **binary giống hệt A** (stage 0 không đổi byte nào). Khác biệt duy nhất có thể đến từ
  import/chuỗi khôi phục được, nếu nhóm bổ sung chúng vào context (bước 3).

## 2. Thiết lập thí nghiệm

| Thành phần | Giá trị | Lý do |
|---|---|---|
| Truy vấn | 50 tên hàm cố định (seed cố định), lấy đều từ 10 chương trình | Dùng **cùng 50 tên** cho cả 4 biến thể và 2 điều kiện, để kết quả so sánh được trực tiếp |
| Điều kiện chọn hàm truy vấn | Có cùng tên trong A (cả 4 biến thể) và B; không phải hàm CRT/thunk (`_start`, `_init`, `frame_dummy`, ...); kích thước ở bản clean ≥ 50 byte | Bỏ hàm quá nhỏ, vốn dễ trùng ngẫu nhiên |
| Tập ứng viên | Toàn bộ hàm (đã lọc như trên) của binary clean **cùng chương trình** trong B | Giống bài toán RQ4: tìm bản gốc của một hàm trong một tập lớn |
| Nhãn | Cùng tên hàm (theo ground truth) → dương, ngược lại → âm | |
| Truy xuất | HermesSim + Context, hệ số α của tác giả (`saved/Binkit-1.0-dataset/pairs/train/model2best_prop-250530.json`) | Cấu hình truy xuất của Co²FuLL |
| Top-K | 5 | Như bài báo và RQ2–RQ4 |
| LLM | `qwen2.5-coder-14b-8k` (Ollama), prompt **Few-Shot**, `top_p=1.0`, `temperature=0.0` | Cùng cấu hình với RQ3/RQ4 (F2 cao nhất ở RQ2) |
| Số cặp gửi LLM | 50 truy vấn × 5 ứng viên × 4 biến thể × 2 điều kiện = **2.000 cặp** | Khoảng 15–25 giây/cặp → khoảng 10 giờ. Có thể giảm còn 30 truy vấn nếu cần |

## 3. Luồng chạy (dùng chung cho RQ5 và RQ6)

Ký hiệu `<S>` là một thư mục binary: `A/<variant>`, `C/<variant>` hoặc `B` (tập ứng viên). RQ6 chỉ cần
chạy các bước này khi D khác B (xem [`../RQ6/README.md`](../RQ6/README.md)), với `<S>` là `B`/`D`.
Các bước 1–4 chạy riêng cho **mỗi** `<S>`. Bước 5–8 chạy một lần cho mỗi điều kiện.

| Bước | Việc | Code | Đầu vào → Đầu ra |
|---|---|---|---|
| 0 | Dựng tập A–D | `Data_RQ5_RQ6/build_sets.py` (**đã chạy**) | `Data_advance/selected_10_O0` → `Data_RQ5_RQ6/` |
| 1 | Tạo IDB | `python IDA_scripts/cli_idbs.py -p Data_RQ5_RQ6/<S>` | binary → `.i64` |
| 2 | Tạo dependency graph (context) | `python IDA_scripts/IDA_DG/cli_DG.py -p Data_RQ5_RQ6/<S>` | `.i64` → `.dg` (import, chuỗi, call graph) |
| 3 | *(chỉ C, D)* Bổ sung context từ stage 0 | **Cần viết**: adapter gọi `preprocessing/inject_context.py::merge_from_output_dir` để thêm `recovered_imports.json` / `recovered_strings.json` của `<S>/stage0/<bin>/` vào `.dg` | `.dg` → `.dg` đã bổ sung |
| 4a | Xuất pseudocode (IDA Hex-Rays) | `python IDA_scripts/IDA_code/cli_code.py -input <json {idb_path: [ea, ...]}>` | → `{"0x<ea>": {"pseudo_code": ...}}` mỗi binary, cùng định dạng `DBs/Binkit-1.0-normal-strip-top_k_code/` |
| 4b | Sinh embedding HermesSim (+ model khác nếu có) | Theo repo HermesSim | → `{"<bin>@0x<ea>": vector}` (`.pkl`) |
| 5 | Chọn truy vấn và dựng cặp | **Cần viết**: `Experiment/scripts/rq56_make_queries.py` (đọc `ground_truth/`, áp điều kiện ở mục 2) | → `Experiment/RQ5/data/queries.csv` |
| 6 | Truy xuất HermesSim+Context, lấy Top-5 | **Cần viết**: `Experiment/scripts/rq56_retrieval.py`, sửa từ `Experiment/scripts/rq4_table3.py` (đã có code tính độ tương đồng model + context với α của tác giả) | → `ranks_<cond>.csv`, `top5_<cond>.csv` (cột như `DBs/xm-full_top5-250515.csv`: `bin_name_1, fva_1, func_name_1, bin_name_2, fva_2, func_name_2, db_type, label, *-sim`) |
| 7 | LLM xác minh Top-5 | `llm_judgement.py`, prompt `few_shot`, `top_p=1.0`, `temperature=0.0`. **Cần chỉnh**: `FUNC_KEY2CODE` đang cố định đọc `DBs/Binkit-1.0-normal-strip-top_k_code/` → cho trỏ tới thư mục pseudocode của bước 4a. `LLM_exp.py` chỉ có `prompt_exp` / `setting_exp` (chạy nhiều prompt/cấu hình), nên nên gọi `llm_judgement.main` qua một wrapper nhỏ chỉ chạy Few-Shot | `top5_<cond>.csv` → `saved/.../rq56/<model>/few_shot-pseudo_code/<cặp>.json` |
| 8 | Tính chỉ số | **Cần viết**: `Experiment/scripts/rq56_metrics.py`, dùng lại `parse()` của `Experiment/scripts/compute_rq_metrics.py` và `utils/metric.py` | → `Experiment/RQ5/data/metrics.csv`, `RQ5_report.md` |

Trong đó `<cond>` là `A_<variant>` hoặc `C_<variant>` (8 điều kiện cho RQ5).

**Về context (bước 2–3):** tập C có thể khác A theo hai đường: binary đã sạch (ảnh hưởng embedding và
pseudocode), và import/chuỗi khôi phục được (ảnh hưởng context). Nếu muốn tách riêng tác dụng của
từng phần, chạy thêm điều kiện "C không có bước 3".

## 4. Chỉ số đo

Báo cáo **tách theo từng biến thể** (`sub`, `bcf`, `fla`, `all`) và thêm một dòng gộp.

| Nhóm | Chỉ số | Cách tính |
|---|---|---|
| Truy xuất | **Recall@1, Recall@5, MRR** | Từ hạng của hàm đúng trong tập ứng viên (như RQ1) |
| LLM xác minh (trên các cặp Top-5) | **Precision, Recall, F2** (β = 2, như bài báo) | Chỉ tính các câu trả lời có thẻ `<same_source>` hợp lệ |
| | Tỉ lệ câu trả lời sai định dạng | Không có thẻ `<same_source>yes/no</same_source>` |
| | **Tỉ lệ prompt vượt 8.192 token** | Ước lượng bằng tokenizer (ví dụ `utils.tool_function.get_tokenizer_num`). Ollama **tự cắt** prompt quá dài mà không báo lỗi, nên pseudocode obfuscate rất dài sẽ bị cắt mất phần sau |
| Toàn pipeline (như RQ4 / Bảng III) | **P, R, F2 với K=5; Nv** | Nv = số ứng viên LLM trả lời "yes", tức số hàm người phân tích phải xem |
| Chẩn đoán stage 0 (giải thích kết quả) | Tỉ lệ detect, số hàm flatten / gỡ hết, số biến opaque, số lệnh đọc opaque đã patch, thời gian stage 0 | Có sẵn trong `Data_RQ5_RQ6/summary.csv` |
| | Độ dài pseudocode của hàm truy vấn (số dòng, số token) ở A so với C | Từ bước 4a |

Trình bày chính: một bảng 4 biến thể × {A, C} × {Recall@5, F2 LLM, F2 toàn pipeline}, kèm cột Δ (C − A).

## 5. Điều cần lưu ý khi viết báo cáo

* **Chỉ `-O0`.** Bộ gỡ flatten chưa hỗ trợ `-O2` (state nằm trong thanh ghi). Xem mục "Giới hạn"
  trong [`preprocessing/README.md`](../../preprocessing/README.md).
* **`sub` không được xử lý.** Stage 0 không đổi byte nào của binary `sub`, và bước detect cũng không
  nhận ra `sub` (0/10, xem `summary.csv`). Nếu C tốt hơn A ở `sub` thì đó là nhờ context bổ sung,
  hoặc do dao động ngẫu nhiên.
* **Compiler khác nhau:** clean là clang 4.0.0, obfuscate là O-LLVM 4.0.1. Một phần khác biệt giữa
  truy vấn và ứng viên đến từ đây, nhưng phần này giống nhau giữa A và C nên không ảnh hưởng tới Δ.
* **Ứng viên là B, không phải D.** Ở thực tế, bước detect sẽ bỏ qua binary clean (0/10 bị nhận nhầm),
  nên ứng viên mà Co²FuLL thấy chính là B. RQ6 kiểm tra xem điều đó có đúng không (detect có nhận
  nhầm không, và nếu ép chạy thì D có khác B không).
* Bài báo **không có** RQ này. Đây là phần mở rộng của nhóm.

## 6. Đầu ra mong đợi (`Experiment/RQ5/data/`)

| File | Nội dung |
|---|---|
| `queries.csv` | 50 truy vấn: chương trình, tên hàm, địa chỉ trong A/C và B, kích thước |
| `ranks_<cond>.csv` | Hạng của hàm đúng cho mỗi truy vấn |
| `top5_<cond>.csv` | Top-5 theo định dạng Co²FuLL (đầu vào của LLM) |
| `llm_<cond>.csv` | Mỗi cặp: nhãn, câu trả lời, giải thích, số token prompt |
| `metrics.csv` | Bảng chỉ số ở mục 4 |
| `../RQ5_report.md` | Báo cáo, theo mẫu RQ1–RQ4 |
