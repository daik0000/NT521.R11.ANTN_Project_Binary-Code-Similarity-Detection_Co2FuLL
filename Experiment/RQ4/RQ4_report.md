# Báo cáo RQ4 — Hiệu quả của Co²FuLL trong bài toán BCSD

> **RQ4.** Co²FuLL hiệu quả đến mức nào trong bài toán BCSD so với các baseline?

**Kết luận ngắn:**
- Trên mẫu 50 query của nhóm, **Co²FuLL với Qwen2.5‑Coder‑14B đạt F2 cao nhất: 85,3%** (bài báo: 88,1%).
- So với chỉ dùng truy xuất HermesSim+Context, Co²FuLL tăng F2 thêm **16,3%** (bài báo: 20,2%) và giảm số hàm cần người kiểm tra (Nv) từ 50 xuống 29, tức **−42%**.
- Các xu hướng sau **khớp với bài báo**:
  - LLM 14B vượt truy xuất đơn thuần; Qwen‑7B thì thấp hơn.
  - Qwen‑7B có Precision cao nhưng Recall thấp.
  - Model suy luận (R1) tốn thời gian nhất.
- **Điểm khác bài báo:** trên mẫu này, HermesSim gốc mạnh bất thường (F2 82,0% khi dùng ngưỡng, so với 55,3% trong bài báo). Vì vậy khoảng cách giữa Co²FuLL và HermesSim nhỏ hơn nhiều so với bài báo. Nguyên nhân là thiên lệch chọn mẫu, phân tích ở mục 4.

---

## 1. Thiết lập

| Mục | Bài báo (Bảng III) | Nhóm |
|---|---|---|
| Tập đánh giá | D1‑XM: 1.000 query × 10.000 ứng viên (10 triệu cặp), 500 query có hàm đích | **50 query của mẫu RQ2** × 10.000 ứng viên = **500.000 cặp**, 25 query có hàm đích |
| Baseline | GMN, Trex, Asteria, Asteria‑Pro, HermesSim, HermesSim+Context | Như bài báo, **trừ Asteria‑Pro**: repo không có mã nguồn và embedding của nó |
| Quét tham số | Ngưỡng T ∈ [0, 1], Top‑K ∈ [1, 50]; báo cấu hình có F2 cao nhất | T từ 0 đến 1, bước 0,05; K từ 1 đến 50. Top‑K giữ cả các ứng viên hòa hạng (`rank(method="min")`), đúng ghi chú "Nv > 1.000 do hòa hạng" của bài báo |
| Co²FuLL | HermesSim+Context lấy Top‑5, rồi LLM Few-Shot (top_p 1.0, temperature 0) | Như bài báo, dùng 4 model cục bộ. Dự đoán lấy lại từ RQ2, **không chạy thêm LLM** |
| Độ đo | P = TP/Nv, R = TP/(số query có hàm đích), F2, Nv = TP + FP | Như bài báo. Phản hồi LLM sai định dạng được tính là "no" (không báo cho người kiểm tra) |

**Cách tính:**
- Độ tương đồng được tính bằng đúng code của repo: `utils/model_sim_rank.py` và `core/context.py`, cùng embedding và DG đã dùng ở RQ1, với α = 0,6 cho HermesSim.
- Script: `Experiment/scripts/rq4_table3.py`. Lần chạy đầu mất ~15 phút; độ tương đồng được lưu đệm tại [data/rq4_sims_50queries.pkl.gz](data/rq4_sims_50queries.pkl.gz), nên các lần chạy sau chỉ mất vài giây.

**Kiểm tra chéo (đều đạt):** [data/rq4_sanity_checks.csv](data/rq4_sanity_checks.csv)
- Thứ hạng của 25 cặp dương tính trên 50 query trùng với thứ hạng trong kết quả RQ1 (tính trên 1.000 query), ở cả 5 phương pháp.
- Top‑5 của HermesSim+Context trùng đúng **250/250 cặp** D2 mà RQ2 đã đưa cho LLM. Nhờ vậy, kết quả LLM của RQ2 dùng được trực tiếp cho RQ4.

---

## 2. Bảng III — kết quả của nhóm so với bài báo

Mỗi ô ghi **Nhóm / Bài báo**. Nv của nhóm tính trên 50 query; Nv của bài báo tính trên 1.000 query.

### Baseline

| Phương pháp | T | P@T | R@T | **F2@T** | Nv@T | K | P@K | R@K | **F2@K** | Nv@K |
|---|---|---|---|---|---|---|---|---|---|---|
| GMN | 1,00 / 0,95 | 100 / 0,2 | 4,0 / 67,0 | **5,0 / 0,8** | 1 / 196.075 | 1 / 1 | 6,0 / 8,9 | 12,0 / 17,8 | **10,0 / 14,8** | 50 / 1.003 |
| Trex | 0,95 / 0,95 | 18,2 / 14,1 | 8,0 / 9,2 | **9,0 / 9,9** | 11 / 326 | 1 / 1 | 10,0 / 10,6 | 20,0 / 21,2 | **16,7 / 17,7** | 50 / 1.002 |
| Asteria | 0,95 / 0,95 | 36,7 / 26,1 | 44,0 / 37,8 | **42,3 / 34,7** | 30 / 725 | 1 / 1 | 32,0 / 24,9 | 64,0 / 50,4 | **53,3 / 41,8** | 50 / 1.011 |
| Asteria‑Pro | – / 0,95 | – / 0,7 | – / 48,0 | **– / 0,8** | – / 33.278 | – / 1 | – / 30,5 | – / 60,0 | **– / 50,3** | – / 984 |
| HermesSim | 0,65 / 0,70 | 75,0 / 26,3 | 84,0 / 67,4 | **82,0 / 51,4** | 28 / 1.279 | 1 / 1 | 46,0 / 33,2 | 92,0 / 66,4 | **76,7 / 55,3** | 50 / 1.000 |
| HermesSim+Context | 0,70 / 0,80 | 72,7 / 48,4 | 64,0 / 61,0 | **65,6 / 58,0** | 22 / 630 | 1 / 1 | 44,0 / 44,0 | 88,0 / 88,0 | **73,3 / 73,3** | 50 / 1.000 |

### Co²FuLL (HermesSim+Context, Top‑5, rồi LLM Few-Shot)

| LLM (nhóm / bài báo) | P@5 | R@5 | **F2@5** | Nv | Thời gian LLM thêm (giờ) |
|---|---|---|---|---|---|
| Qwen2.5‑7B | 100 / 91,4 | 48,0 / 67,8 | **53,6 / 71,5** | 12 / 371 | 1,8 / 3,3 |
| Qwen2.5‑Coder‑14B | 75,9 / 86,7 | 88,0 / 88,4 | **85,3 / 88,1** | 29 / 510 | 3,3 / 4,7 |
| Qwen2.5‑14B | 66,7 / 83,0 | 88,0 / 89,8 | **82,7 / 88,4** | 33 / 541 | 3,5 / 4,8 |
| DeepSeek‑R1‑14B (distill) / DeepSeek‑R1 | 65,6 / 50,6 | 84,0 / 96,2 | **79,6 / 81,5** | 32 / 951 | 15,3 / 48,8 |
| Qwen‑72B / GPT‑4o / DeepSeek‑V3 | – | – | **– / 90,3 · 88,7 · 91,2** | – | – |

Ghi chú về các cột:
- **Thời gian LLM thêm:** của nhóm là tổng thời gian gọi model trên 250 cặp, chạy CPU cục bộ. Của bài báo là thời gian gọi API trên ~5.000 cặp. Hai con số không so sánh trực tiếp được.
- **Chi phí tiền:** nhóm không có (chạy cục bộ).
- **Thời gian FG/Matching của baseline:** nhóm không đo.

Dữ liệu: [data/rq4_table3.csv](data/rq4_table3.csv). Toàn bộ đường quét T/K: [data/rq4_baseline_sweep.csv](data/rq4_baseline_sweep.csv).

---

## 3. Đối chiếu các nhận định của bài báo

| Nhận định của bài báo | Kết quả của nhóm | Đánh giá |
|---|---|---|
| Baseline yếu cho F2 thấp ngay cả khi chọn T/K tốt nhất (GMN, Trex < 18%) | GMN 10,0%, Trex 16,7% | Khớp |
| Top‑K tốt hơn lọc theo ngưỡng, vì ngưỡng cần Nv rất lớn mới đạt recall cao | Đúng với GMN, Trex, Asteria và HermesSim+C. Riêng HermesSim gốc: lọc theo ngưỡng (82,0) tốt hơn Top‑K (76,7) | Khớp phần lớn |
| HermesSim+Context đạt F2 73,3%, cao hơn HermesSim 32,5% | Đúng 73,3%, nhưng **thấp hơn** HermesSim gốc (F2@T 82,0; F2@K 76,7) | Không khớp (xem mục 4) |
| Co²FuLL với LLM mạnh vượt mọi baseline | Coder‑14B 85,3 và Qwen‑14B 82,7 đều ≥ baseline tốt nhất (HermesSim 82,0) | Khớp, nhưng cách biệt nhỏ |
| LLM giúp tăng F2 so với HermesSim+Context đơn thuần | Coder‑14B +16,3%, Qwen‑14B +12,8%, R1‑14B +8,5% (bài báo: +20,2%, +20,6%, +11,2%) | Khớp |
| Qwen‑7B làm F2 giảm so với HermesSim+C (71,5 < 73,3): Precision cao, Recall thấp | 53,6 < 73,3, với P 100% và R 48% | Khớp, mức giảm lớn hơn |
| R1 có Recall cao nhất nhưng Precision thấp nhất và Nv lớn nhất | R1‑14B: Precision thấp nhất (65,6), nhưng Recall không cao nhất (84 so với 88) | Khớp một phần |
| LLM giảm Nv (DeepSeek‑V3: 1.000 → 586, −41,4%) | Coder‑14B: 50 → 29 (−42%); Qwen‑14B: −34%; R1‑14B: −36% | Khớp |
| Chi phí thêm nhỏ vì LLM chỉ xét Top‑5; R1 tốn nhất | Thời gian LLM tỉ lệ với số query (5 cặp mỗi query); R1‑14B tốn gấp ~4–9 lần các model khác | Khớp |

---

## 4. Vì sao HermesSim gốc mạnh bất thường trên mẫu này

| Chỉ số (XM) | 500 query có hàm đích (RQ1) | 25 query có hàm đích của mẫu |
|---|---|---|
| HermesSim R@1 | 66,4% | **92,0%** |
| HermesSim+Context R@1 | 88,0% | 88,0% |

1. **Mẫu chỉ gồm 2 project** (a2ps và binutils), được lấy theo thứ tự file chứ không lấy ngẫu nhiên. Với các hàm của hai project này, embedding HermesSim gốc đã phân biệt rất tốt, nên ngữ cảnh không còn nhiều chỗ để cải thiện. Trên toàn bộ D1, ngữ cảnh tăng R@1 từ 66,4% lên 88,0%; trên mẫu này lại giảm nhẹ từ 92% xuống 88%.
2. **Mẫu chỉ chứa query mà hàm đích nằm trong Top‑5 của HermesSim+Context.** Trên D1 có ~1,8% query bị Top‑5 bỏ sót hàm đích, và những query này không có trong mẫu. Vì vậy, Recall tối đa của Co²FuLL trên mẫu là 100%, so với 98,2% trên D1.
3. **T và K được chọn trên chính 50 query đánh giá.** Bài báo cũng chọn trên tập test, nhưng với chỉ 25 cặp dương, cấu hình "tốt nhất" dễ bị quá khớp. Ví dụ, F2 của HermesSim giảm từ 82,0 xuống 73,9 khi đổi T từ 0,65 sang 0,60, và xuống 75,0 khi đổi sang 0,70.

Vì vậy, kết quả RQ4 của nhóm nên được trình bày là **khớp xu hướng của phần LLM**: LLM tăng F2 và giảm Nv so với truy xuất đơn thuần. Phần so sánh baseline thì chưa đại diện được cho D1.

---

## 5. Các điểm kỹ thuật cần ghi nhận

- **Asteria thiếu embedding cho 1 query trong mẫu** (`binutils-2.30_clang-4.0_arm_32_O2_objdump.elf.strip@0x7267c`); trên 500 query có hàm đích của D1, có 2 query bị thiếu. Với query này, mọi ứng viên có cùng độ tương đồng nên đều hòa ở hạng 1. Lần chạy đầu tính cả 10.000 cặp đó vào Nv@K, khiến F2@K của Asteria chỉ còn ~1%. Nhóm coi trường hợp này là "phương pháp không trả về ứng viên" (P/R/F2 đã tính lại như trong bảng). Trong RQ1, query này có hạng trung bình 5.000,5, đúng như dự kiến. Đây cũng là hàm rất dài xuất hiện trong 2 cặp LLM phân loại sai ở RQ3.
- **GMN:** độ tương đồng tập trung sát 1,0, nên bước ngưỡng 0,05 quá thô (T tốt nhất là 1,00, Nv = 1). Bài báo cũng ghi nhận GMN có F2@T rất thấp (0,8%).
- **Asteria‑Pro:** không tái hiện được. Bảng trên giữ nguyên số của bài báo để tham khảo.

## 6. Kết luận

Trong phạm vi 50 query, nhóm tái hiện được câu trả lời RQ4 của bài báo ở **phần đóng góp của LLM**: Co²FuLL với LLM 14B (Coder‑14B, Qwen‑14B) đạt F2 cao nhất và giảm khoảng 35–42% số hàm cần kiểm tra thủ công. Giá trị F2 của Coder‑14B (85,3%) và R1 (79,6%) cũng gần với bài báo (88,1% và 81,5%). Ngược lại, khoảng cách lớn giữa Co²FuLL và HermesSim gốc như trong bài báo **không xuất hiện** trên mẫu này. Lý do là các query của a2ps và binutils vốn dễ với HermesSim, nên ngữ cảnh không còn tạo ra khác biệt như trên toàn bộ D1.
