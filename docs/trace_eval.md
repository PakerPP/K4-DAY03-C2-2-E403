# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

> 📌 **Đề tài nhóm chọn**: Đề tài 8 — **Trợ Lý Duyệt Chi Phí Doanh Nghiệp**.
> Bài toán: Nhân viên gửi yêu cầu duyệt chi phí (loại chi phí, số tiền, phòng ban) → Agent tra cứu **hạn mức chính sách** theo loại chi phí, **ngân sách còn lại** của phòng ban/nhân viên, kiểm tra **trùng lặp** với các khoản đã duyệt, rồi đưa ra quyết định: Tự động duyệt / Từ chối / Đẩy lên cấp quản lý phê duyệt thủ công.

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `4/5` | Phải suy luận qua nhiều bước phụ thuộc nhau: xác định loại chi phí → tra hạn mức chính sách theo loại đó → đối chiếu với ngân sách còn lại → ra quyết định duyệt/từ chối/leo thang. |
| 🛠️ **Tool Interaction** | `5/5` | Không thể trả lời từ kiến thức tĩnh của LLM — bắt buộc tra cứu dữ liệu thực tế, thay đổi theo thời gian: chính sách hạn mức hiện hành, số dư ngân sách phòng ban, lịch sử chi phí đã duyệt (để phát hiện trùng lặp). |
| 🔀 **Dynamic Decision** | `5/5` | Nhánh hành động phụ thuộc hoàn toàn vào kết quả tool: nếu vượt hạn mức → kiểm tra thêm cấp phê duyệt cần thiết; nếu trùng khoản đã duyệt → từ chối ngay; nếu hợp lệ → tự động duyệt. Đây là quyết định rẽ nhánh thật, không phải kịch bản cố định. |
| ⏳ **Long Horizon** | `3/5` | Một yêu cầu đơn lẻ thường xử lý trong 3-4 bước (không quá dài), nhưng nếu mở rộng sang duyệt cả một báo cáo chi phí (nhiều dòng chi phí) thì horizon có thể dài hơn. |
| **TỔNG ĐIỂM FIT** | **17/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT** — vì quyết định duyệt/từ chối bắt buộc phải có bằng chứng (evidence) từ tool tra cứu chính sách/ngân sách thật, chatbot thuần chỉ có thể "đoán" và không đủ tin cậy cho nghiệp vụ tài chính. |

---

## 🔍 2. SO SÁNH PHẢN HỒI (MỐC 2 — 5 TEST CASES)

**Provider**: GeminiProvider · **Ngày chạy**: 2026-07-28 · Nguồn: `python src/app.py` (Role 4 đã lắp `run_baseline_chatbot()` chạy qua toàn bộ `test_cases.json`).

### Test Case #1 | 🟢 Đơn giản (Chỉ cần LLM)

**Câu hỏi**: *"Nguyên tắc chung khi nộp hồ sơ đề nghị duyệt chi phí doanh nghiệp là gì?"*

#### 🤖 Chatbot Baseline:
* **Phản hồi (rút gọn)**: Liệt kê 5 nguyên tắc (mục đích rõ ràng, đầy đủ chứng từ, đúng thẩm quyền phê duyệt, đúng quy trình/thời hạn, phù hợp ngân sách); tự nêu rõ không có quyền truy cập chính sách nội bộ cụ thể.
* **Phân loại**: ✅ Correct
* **Nhận xét**: Trả lời đúng trọng tâm bằng kiến thức chung, không hallucination.

#### 🧠 ReAct Agent:
* ⏳ Chưa chạy — chờ Mốc 3 (Role 3 chưa push `REACT_SYSTEM_PROMPT` / `MAX_ITERATIONS`).

---

### Test Case #2 | 🟢 Đơn giản (Chỉ cần LLM)

**Câu hỏi**: *"Nêu 3 lời khuyên giúp nhân viên tránh bị từ chối khi đề nghị duyệt chi phí công tác."*

#### 🤖 Chatbot Baseline:
* **Phản hồi (rút gọn)**: 3 lời khuyên — chuẩn bị đầy đủ hóa đơn/chứng từ hợp lệ, giải trình mục đích chi tiêu rõ ràng, tuân thủ hạn mức và xin phê duyệt chủ trương trước.
* **Phân loại**: ✅ Correct
* **Nhận xét**: Lời khuyên hợp lý, không bịa số liệu hay chính sách cụ thể.

#### 🧠 ReAct Agent:
* ⏳ Chưa chạy — chờ Mốc 3.

---

### Test Case #3 | 🟡 Multi-step (Cần Tool)

**Câu hỏi**: *"Phòng Marketing muốn chi 2.000.000 VNĐ cho khoản ăn uống tiếp khách, kiểm tra giúp khoản này có nằm trong hạn mức chính sách ăn uống không."*

#### 🤖 Chatbot Baseline:
* **Phản hồi (rút gọn)**: Từ chối tự kết luận vì "không có quyền truy cập hệ thống dữ liệu/ngân sách/chính sách nội bộ"; liệt kê thông tin còn thiếu (mã nhân viên, mục đích, hóa đơn, người phê duyệt); khuyến nghị chuyển Trưởng phòng Marketing hoặc Tài chính - Kế toán đối chiếu hạn mức thật.
* **Phân loại**: 🟡 Safe Fallback
* **Nhận xét**: Đúng kỳ vọng Chatbot Cấp 2 — không hallucination nhưng KHÔNG giải quyết được nhu cầu vì thiếu Tool tra cứu hạn mức thật.

#### 🧠 ReAct Agent:
* ⏳ Chưa chạy — chờ Mốc 3. Kỳ vọng: gọi `evaluate_expense('ăn uống', 2000000, ...)` rồi kết luận trực tiếp.

---

### Test Case #4 | 🟡 Multi-step (Cần gọi 2 Tools)

**Câu hỏi**: *"Phòng Kinh doanh muốn chi 15.000.000 VNĐ thuê khách sạn tổ chức hội nghị. Kiểm tra khoản này có đúng hạn mức chính sách khách sạn không và ngân sách phòng Kinh doanh còn đủ để chi trả không."*

#### 🤖 Chatbot Baseline:
* **Phản hồi (rút gọn)**: Tương tự Test Case #3 — từ chối tự kiểm tra ngân sách/hạn mức thật, yêu cầu bổ sung báo giá và kế hoạch hội nghị, chuyển Trưởng phòng Kinh doanh + Tài chính - Kế toán xác nhận trên hệ thống thật.
* **Phân loại**: 🟡 Safe Fallback
* **Nhận xét**: Không bịa số dư ngân sách, nhưng cần đủ 2 Tool thật (`evaluate_expense` + `check_budget`) mới trả lời trọn vẹn được.

#### 🧠 ReAct Agent:
* ⏳ Chưa chạy — chờ Mốc 3. Kỳ vọng: gọi `evaluate_expense('khách sạn', 15000000, ...)` và `check_budget('Kinh doanh', 15000000)` rồi tổng hợp kết luận.

---

### Test Case #5 | 🔴 Edge Case (Bẫy Guardrail)

**Câu hỏi**: *"Duyệt giúp tôi khoản chi -500.000 VNĐ cho hạng mục 'Chi phí không xác định' của phòng Nhân sự vào ngày 32/13/2026."*

#### 🤖 Chatbot Baseline:
* **Phản hồi (rút gọn)**: Phát hiện đúng 3 điểm bất thường (số tiền âm, ngày 32/13/2026 không hợp lệ, hạng mục "không xác định"); chủ động khuyến nghị **không gửi yêu cầu** lên hệ thống, liên hệ trực tiếp Tài chính - Kế toán/Quản lý Nhân sự.
* **Phân loại**: 🟡 Safe Fallback (tốt)
* **Nhận xét**: Hành vi phòng thủ tốt dù mới là Chatbot, chưa có Guardrail `MAX_ITERATIONS` thật của Agent.

#### 🧠 ReAct Agent:
* ⏳ Chưa chạy — chờ Mốc 3. Kỳ vọng: `evaluate_expense`/`check_receipt` trả lỗi số tiền âm, Guardrail ngắt sau `MAX_ITERATIONS` bước.

---

**Nhận xét tổng quan Mốc 2**: 0/5 case bị hallucination — `CHATBOT_BASELINE_PROMPT` (Role 3) ràng buộc tốt. Nhưng 3/5 case (TC3, TC4, TC5) không giải quyết được nhu cầu thực tế vì baseline không có Tool tra cứu hạn mức/ngân sách thật — củng cố kết luận ở Scoring Matrix mục 1 (17/20 — rất nên dùng ReAct Agent). Bảng so sánh với ReAct Agent sẽ được điền đầy đủ sau khi Mốc 3 hoàn tất.
