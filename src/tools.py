"""
🛠️ TOOL REGISTRY & SCHEMAS

Các công cụ hỗ trợ ReAct Agent kiểm tra, đánh giá và xử lý
yêu cầu duyệt chi phí trong doanh nghiệp.

Lưu ý:
- Dữ liệu trong file hiện tại là dữ liệu mô phỏng phục vụ bài lab.
- Tool chỉ hỗ trợ kiểm tra và đề xuất, không thay thế người có thẩm quyền.
"""


def _required_text(value, field_name: str):
    """Chuẩn hóa chuỗi bắt buộc; trả về thông báo lỗi nếu không hợp lệ."""
    if not isinstance(value, str) or not value.strip():
        return None, f"LỖI: {field_name} phải là chuỗi không được để trống."
    return value.strip(), None


def _positive_amount(value, field_name: str = "Số tiền"):
    """Chuẩn hóa số tiền dương và loại trừ bool/NaN/giá trị sai kiểu."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, f"LỖI: {field_name} phải là một số."
    if value != value or value <= 0:
        return None, f"LỖI: {field_name} phải lớn hơn 0."
    return float(value), None


def get_expense_policy(expense_type: str) -> str:
    """
    Tra cứu chính sách và hạn mức áp dụng cho một loại chi phí.

    Tool được sử dụng khi Agent cần xác định một khoản chi có thuộc
    danh mục được doanh nghiệp hỗ trợ hay không và hạn mức tương ứng.

    Args:
        expense_type (str): Loại chi phí cần tra cứu.
            Ví dụ: "ăn uống", "di chuyển", "khách sạn",
            "văn phòng phẩm".

    Returns:
        str: Nội dung chính sách, hạn mức và yêu cầu chứng từ.
        Nếu loại chi phí không tồn tại, trả về chuỗi bắt đầu bằng "LỖI:".

    Failure Modes:
        - Loại chi phí bị bỏ trống.
        - Loại chi phí không tồn tại trong dữ liệu.
        - Người dùng nhập tên chi phí không đúng định dạng.
        - Chính sách trong hệ thống chưa được cập nhật.
    """
    expense_type, error = _required_text(expense_type, "Loại chi phí")
    if error:
        return error
    expense_type_lower = expense_type.lower()

    policies = {
        "ăn uống": (
            "Chi phí ăn uống: Tối đa 300.000 VNĐ/người/ngày. "
            "Bắt buộc có hóa đơn nếu giá trị từ 200.000 VNĐ."
        ),
        "di chuyển": (
            "Chi phí di chuyển: Tối đa 1.500.000 VNĐ/chuyến công tác. "
            "Cần cung cấp vé hoặc hóa đơn."
        ),
        "khách sạn": (
            "Chi phí khách sạn: Tối đa 1.200.000 VNĐ/lần đặt phòng. "
            "Cần có hóa đơn và thông tin chuyến công tác."
        ),
        "văn phòng phẩm": (
            "Chi phí văn phòng phẩm: Tối đa 2.000.000 VNĐ/tháng/phòng ban. "
            "Khoản chi trên 1.000.000 VNĐ cần trưởng phòng phê duyệt."
        ),
    }

    for key, policy in policies.items():
        if key in expense_type_lower:
            return policy

    return (
        f"LỖI: Không tìm thấy chính sách cho loại chi phí "
        f"'{expense_type}'."
    )


def check_receipt(
    receipt_id: str,
    amount: float,
    has_receipt: bool
) -> str:
    """
    Kiểm tra tính đầy đủ cơ bản của hóa đơn hoặc chứng từ chi phí.

    Tool kiểm tra số tiền, trạng thái cung cấp hóa đơn và mã hóa đơn.
    Tool không xác minh được hóa đơn thật hay giả trong phiên bản mô phỏng.

    Args:
        receipt_id (str): Mã định danh của hóa đơn hoặc chứng từ.
        amount (float): Tổng số tiền ghi trên hóa đơn, đơn vị VNĐ.
        has_receipt (bool): Cho biết người dùng đã cung cấp hóa đơn hay chưa.

    Returns:
        str: Kết quả kiểm tra hóa đơn:
            - "HỢP LỆ:" nếu thông tin cơ bản đầy đủ.
            - "KHÔNG HỢP LỆ:" nếu thiếu chứng từ bắt buộc.
            - "LỖI:" nếu dữ liệu đầu vào không hợp lệ.

    Failure Modes:
        - Số tiền bằng 0 hoặc nhỏ hơn 0.
        - Có hóa đơn nhưng thiếu mã hóa đơn.
        - Khoản chi bắt buộc có hóa đơn nhưng không cung cấp.
        - Mã hóa đơn bị nhập sai hoặc không đọc được.
    """
    amount, error = _positive_amount(amount, "Số tiền trên hóa đơn")
    if error:
        return error

    if not isinstance(has_receipt, bool):
        return "LỖI: Trạng thái hóa đơn phải là true hoặc false."

    if receipt_id is None:
        receipt_id = ""
    if not isinstance(receipt_id, str):
        return "LỖI: Mã hóa đơn phải là chuỗi."

    if amount >= 200_000 and not has_receipt:
        return (
            "KHÔNG HỢP LỆ: Khoản chi từ 200.000 VNĐ "
            "trở lên bắt buộc phải có hóa đơn."
        )

    if has_receipt and not receipt_id.strip():
        return "LỖI: Có hóa đơn nhưng chưa cung cấp mã hóa đơn."

    return (
        f"HỢP LỆ: Hóa đơn '{receipt_id}' đã được kiểm tra. "
        f"Số tiền: {amount:,.0f} VNĐ."
    )


def check_budget(
    department: str,
    requested_amount: float
) -> str:
    """
    Kiểm tra ngân sách còn lại của phòng ban trước khi duyệt chi.

    Tool so sánh số tiền được đề nghị với ngân sách hiện có của
    phòng ban tương ứng.

    Args:
        department (str): Tên phòng ban chịu trách nhiệm cho khoản chi.
            Ví dụ: "Marketing", "Nhân sự", "Công nghệ", "Kinh doanh".
        requested_amount (float): Số tiền đề nghị thanh toán, đơn vị VNĐ.

    Returns:
        str: Kết quả kiểm tra ngân sách:
            - "ĐỦ NGÂN SÁCH:" nếu có thể chi trả.
            - "KHÔNG ĐỦ NGÂN SÁCH:" nếu số tiền vượt ngân sách.
            - "LỖI:" nếu dữ liệu phòng ban hoặc số tiền không hợp lệ.

    Failure Modes:
        - Phòng ban không tồn tại trong hệ thống.
        - Số tiền yêu cầu không hợp lệ.
        - Dữ liệu ngân sách chưa được cập nhật.
        - Hai yêu cầu đồng thời sử dụng cùng một phần ngân sách.
    """
    budgets = {
        "marketing": 20_000_000,
        "nhân sự": 10_000_000,
        "công nghệ": 30_000_000,
        "kinh doanh": 25_000_000,
    }

    department, error = _required_text(department, "Tên phòng ban")
    if error:
        return error
    department_lower = department.lower()

    requested_amount, error = _positive_amount(requested_amount)
    if error:
        return error

    if department_lower not in budgets:
        return (
            f"LỖI: Không tìm thấy dữ liệu ngân sách "
            f"của phòng ban '{department}'."
        )

    remaining_budget = budgets[department_lower]

    if requested_amount > remaining_budget:
        return (
            f"KHÔNG ĐỦ NGÂN SÁCH: Phòng {department} còn "
            f"{remaining_budget:,.0f} VNĐ nhưng yêu cầu "
            f"{requested_amount:,.0f} VNĐ."
        )

    budget_after = remaining_budget - requested_amount

    return (
        f"ĐỦ NGÂN SÁCH: Phòng {department} còn "
        f"{remaining_budget:,.0f} VNĐ. Sau khoản chi sẽ còn "
        f"{budget_after:,.0f} VNĐ."
    )


def detect_duplicate_expense(
    employee_id: str,
    receipt_id: str,
    amount: float
) -> str:
    """
    Phát hiện yêu cầu thanh toán có khả năng bị gửi trùng lặp.

    Tool so sánh mã nhân viên, mã hóa đơn và số tiền với các yêu cầu
    đã tồn tại trong hệ thống mô phỏng.

    Args:
        employee_id (str): Mã nhân viên gửi yêu cầu thanh toán.
        receipt_id (str): Mã hóa đơn hoặc chứng từ.
        amount (float): Số tiền đề nghị thanh toán, đơn vị VNĐ.

    Returns:
        str: Kết quả kiểm tra:
            - "PHÁT HIỆN TRÙNG LẶP:" nếu tìm thấy yêu cầu giống nhau.
            - "KHÔNG TRÙNG LẶP:" nếu chưa tìm thấy yêu cầu tương tự.
            - "LỖI:" nếu dữ liệu đầu vào không hợp lệ.

    Failure Modes:
        - Thiếu mã nhân viên hoặc mã hóa đơn.
        - Mã hóa đơn có nhiều cách viết khác nhau.
        - Không truy cập được lịch sử yêu cầu.
        - Hai khoản chi hợp lệ vô tình có cùng số tiền.
    """
    employee_id, error = _required_text(employee_id, "Mã nhân viên")
    if error:
        return error

    receipt_id, error = _required_text(receipt_id, "Mã hóa đơn")
    if error:
        return error

    amount, error = _positive_amount(amount)
    if error:
        return error

    submitted_expenses = [
        {
            "employee_id": "NV001",
            "receipt_id": "HD1001",
            "amount": 500_000,
        },
        {
            "employee_id": "NV002",
            "receipt_id": "HD1002",
            "amount": 1_200_000,
        },
    ]

    for expense in submitted_expenses:
        if (
            expense["employee_id"].lower() == employee_id.lower()
            and expense["receipt_id"].lower() == receipt_id.lower()
            and expense["amount"] == amount
        ):
            return (
                "PHÁT HIỆN TRÙNG LẶP: Khoản chi này đã được "
                "gửi trước đó."
            )

    return "KHÔNG TRÙNG LẶP: Chưa tìm thấy yêu cầu tương tự."


def evaluate_expense(
    expense_type: str,
    amount: float,
    business_purpose: str
) -> str:
    """
    Đánh giá sơ bộ tính hợp lệ của một khoản chi doanh nghiệp.

    Tool kiểm tra loại chi phí, hạn mức và mục đích sử dụng.
    Kết quả chỉ mang tính đề xuất, không phải quyết định phê duyệt cuối cùng.

    Args:
        expense_type (str): Loại chi phí cần đánh giá.
        amount (float): Số tiền đề nghị thanh toán, đơn vị VNĐ.
        business_purpose (str): Mô tả mục đích sử dụng khoản chi.

    Returns:
        str: Kết quả đánh giá:
            - "ĐỦ ĐIỀU KIỆN:" nếu đáp ứng quy tắc cơ bản.
            - "VƯỢT HẠN MỨC:" nếu số tiền vượt mức cho phép.
            - "CẦN DUYỆT THỦ CÔNG:" nếu không xác định được chính sách.
            - "TỪ CHỐI:" nếu thông tin bắt buộc không hợp lệ.

    Failure Modes:
        - Thiếu mục đích chi tiêu.
        - Số tiền không hợp lệ.
        - Loại chi phí chưa được định nghĩa.
        - Hạn mức áp dụng khác nhau giữa các phòng ban.
    """
    expense_type, error = _required_text(expense_type, "Loại chi phí")
    if error:
        return error

    amount, error = _positive_amount(amount)
    if error:
        return error

    business_purpose, error = _required_text(
        business_purpose, "Mục đích sử dụng"
    )
    if error:
        return error

    limits = {
        "ăn uống": 300_000,
        "di chuyển": 1_500_000,
        "khách sạn": 1_200_000,
        "văn phòng phẩm": 2_000_000,
    }

    expense_type_lower = expense_type.lower()

    if expense_type_lower not in limits:
        return (
            f"CẦN DUYỆT THỦ CÔNG: Không xác định được hạn mức "
            f"cho loại chi phí '{expense_type}'."
        )

    limit = limits[expense_type_lower]

    if amount > limit:
        return (
            f"VƯỢT HẠN MỨC: Khoản chi {amount:,.0f} VNĐ vượt "
            f"hạn mức {limit:,.0f} VNĐ. Cần quản lý phê duyệt."
        )

    return (
        f"ĐỦ ĐIỀU KIỆN: Khoản chi thuộc loại '{expense_type}', "
        f"không vượt hạn mức và có mục đích hợp lệ."
    )


def submit_expense_approval(
    employee_id: str,
    expense_type: str,
    amount: float,
    approver_id: str
) -> str:
    """
    Tạo và gửi yêu cầu duyệt chi phí đến người có thẩm quyền.

    Tool chỉ được gọi sau khi các thông tin cơ bản của khoản chi
    đã được kiểm tra.

    Args:
        employee_id (str): Mã nhân viên gửi yêu cầu.
        expense_type (str): Loại chi phí cần phê duyệt.
        amount (float): Số tiền đề nghị thanh toán, đơn vị VNĐ.
        approver_id (str): Mã nhân viên của người phê duyệt.

    Returns:
        str: Thông báo tạo yêu cầu thành công cùng mã yêu cầu.
        Trả về "LỖI:" nếu thiếu thông tin hoặc dữ liệu không hợp lệ.

    Failure Modes:
        - Thiếu mã nhân viên.
        - Thiếu mã người phê duyệt.
        - Người được chọn không có quyền phê duyệt.
        - Số tiền không hợp lệ.
        - Hệ thống không thể lưu yêu cầu.
    """
    employee_id, error = _required_text(employee_id, "Mã nhân viên")
    if error:
        return error

    expense_type, error = _required_text(expense_type, "Loại chi phí")
    if error:
        return error

    approver_id, error = _required_text(approver_id, "Mã người phê duyệt")
    if error:
        return error

    amount, error = _positive_amount(amount)
    if error:
        return error

    request_id = "EXP-2026-001"

    return (
        f"ĐÃ GỬI YÊU CẦU: Mã yêu cầu {request_id}. "
        f"Nhân viên {employee_id} đề nghị duyệt "
        f"{amount:,.0f} VNĐ cho chi phí '{expense_type}'. "
        f"Người duyệt: {approver_id}."
    )


def get_approval_status(request_id: str) -> str:
    """
    Tra cứu trạng thái xử lý của một yêu cầu duyệt chi phí.

    Args:
        request_id (str): Mã định danh của yêu cầu duyệt chi phí.
            Ví dụ: "EXP-2026-001".

    Returns:
        str: Trạng thái hiện tại của yêu cầu.
        Nếu không tìm thấy yêu cầu, trả về chuỗi bắt đầu bằng "LỖI:".

    Failure Modes:
        - Mã yêu cầu bị bỏ trống.
        - Mã yêu cầu không tồn tại.
        - Trạng thái chưa được đồng bộ.
        - Yêu cầu đã bị xóa hoặc hủy.
    """
    approval_requests = {
        "EXP-2026-001": "Đang chờ trưởng phòng phê duyệt",
        "EXP-2026-002": "Đã được phê duyệt",
        "EXP-2026-003": "Đã bị từ chối do thiếu hóa đơn",
    }

    request_id, error = _required_text(request_id, "Mã yêu cầu duyệt chi phí")
    if error:
        return error
    request_id_upper = request_id.upper()

    if request_id_upper not in approval_requests:
        return f"LỖI: Không tìm thấy yêu cầu có mã '{request_id}'."

    return (
        f"Trạng thái yêu cầu {request_id_upper}: "
        f"{approval_requests[request_id_upper]}."
    )


AVAILABLE_TOOLS = {
    "get_expense_policy": get_expense_policy,
    "check_receipt": check_receipt,
    "check_budget": check_budget,
    "detect_duplicate_expense": detect_duplicate_expense,
    "evaluate_expense": evaluate_expense,
    "submit_expense_approval": submit_expense_approval,
    "get_approval_status": get_approval_status,
}
