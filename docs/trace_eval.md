# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

> 📌 **Đề tài nhóm chọn**: Đề tài 8 — **Trợ Lý Duyệt Chi Phí Doanh Nghiệp** (Enterprise Expense Approval Assistant).
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

> 💡 **Gợi ý bàn giao cho Role 2 (Tool Engineer)** — các tool có thể cần cho đề tài này:
> - `check_expense_policy(category, amount)` → trả về hạn mức cho phép theo loại chi phí (ăn uống, đi lại, khách sạn, thiết bị...).
> - `get_department_budget(department)` → tra số ngân sách còn lại của phòng ban.
> - `check_duplicate_expense(employee_id, amount, date)` → kiểm tra chi phí trùng lặp đã được duyệt trước đó.
>
> 💡 **Gợi ý bàn giao cho Role 3 (Prompt & Safeguard Engineer)** — các Failure Mode cần lường trước:
> - Loại chi phí không tồn tại trong danh mục chính sách.
> - Số tiền âm hoặc bằng 0 (dữ liệu vô lý).
> - Ngân sách phòng ban không tồn tại / phòng ban nhập sai tên.
> - Agent lặp vô hạn khi cứ tra đi tra lại cùng 1 chi phí (guardrail `MAX_ITERATIONS`).

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

> ⚠️ **Ghi chú (Mốc 1)**: Nội dung Test Case #3 bên dưới là **ví dụ mẫu của giảng viên** (chủ đề thời tiết/chuyến bay), giữ lại để tham khảo định dạng báo cáo. Sau khi Role 1 hoàn thiện `config/test_cases.json` cho đề tài 8 ở **Mốc 2**, phần này sẽ được thay bằng trace thật của Agent Duyệt Chi Phí.

**Câu hỏi**: *"Thời tiết ở Hà Nội hôm nay thế nào và tôi nên mặc gì đi chơi?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Tôi không có truy cập Internet thời gian thực nên không biết thời tiết hôm nay ở Hà Nội."*
* **Nhận xét**: An toàn nhưng không giải quyết được nhu cầu thực tế của người dùng.

### 🧠 ReAct Agent:
* **Thought 1**: Cần tra cứu thời tiết Hà Nội.
* **Action 1**: `get_weather['Hà Nội']`
* **Observation 1**: `Thời tiết Hà Nội: 28°C, Nắng nhẹ, Độ ẩm 65%.`
* **Thought 2**: Đã có thông tin 28°C nắng nhẹ, đưa ra lời khuyên trang phục.
* **Final Answer**: *"Thời tiết Hà Nội hôm nay 28°C, nắng nhẹ. Bạn nên mặc quần áo thoáng mát!"*
* **Nhận xét**: Hoàn thành xuất sắc nhiệm vụ nhờ sự kết hợp giữa suy luận và công cụ.
