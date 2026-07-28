"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.

Chủ đề nhóm: TRỢ LÝ DUYỆT CHI PHÍ DOANH NGHIỆP (Expense Approval Agent)
Trạng thái: Mốc 2 - Baseline Chatbot đã chạy. ReAct Loop sẽ lắp ở Mốc 3.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT
from providers import get_llm_provider

# Role 3 sẽ bổ sung REACT_SYSTEM_PROMPT & MAX_ITERATIONS ở Mốc 3.
# Dùng giá trị tạm để app vẫn chạy được Baseline Chatbot khi chưa có.
try:
    from prompts import REACT_SYSTEM_PROMPT, MAX_ITERATIONS
    REACT_PROMPT_READY = True
except ImportError:
    REACT_SYSTEM_PROMPT = ""
    MAX_ITERATIONS = 5
    REACT_PROMPT_READY = False

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Dựng Chatbot gốc (Baseline - Cấp 2) không có công cụ.

    Chatbot này chỉ dùng kiến thức tĩnh của LLM, không truy cập được
    chính sách/ngân sách nội bộ trong tools.py. Đây chính là bằng chứng
    cho thấy bài toán duyệt chi phí BẮT BUỘC phải dùng Agent.

    Returns:
        str: Câu trả lời của Chatbot (Role 5 copy đoạn này vào trace_eval.md).
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")

    try:
        response = provider.generate(
            user_query,
            system_prompt=CHATBOT_BASELINE_PROMPT
        )
    except Exception as e:
        response = f"[Lỗi gọi LLM]: {e}"

    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def run_react_agent(user_query: str, provider) -> str:
    """
    Vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.

    ⚠️ CHƯA TRIỂN KHAI - Đây là nhiệm vụ của Mốc 3.
    Điều kiện cần: Role 3 push REACT_SYSTEM_PROMPT & MAX_ITERATIONS vào prompts.py.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    if not REACT_PROMPT_READY:
        msg = (
            "⏳ ReAct Agent chưa sẵn sàng: prompts.py chưa có "
            "REACT_SYSTEM_PROMPT / MAX_ITERATIONS (Role 3 - Mốc 3)."
        )
        print(msg)
        return msg

    msg = "⏳ ReAct Loop sẽ được lắp ráp ở Mốc 3."
    print(msg)
    return msg


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("📌 Chủ đề: Trợ Lý Duyệt Chi Phí Doanh Nghiệp")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    print(f"🛠️ Đã nạp {len(AVAILABLE_TOOLS)} tools: {', '.join(AVAILABLE_TOOLS.keys())}")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json")

    # MỐC 2: Chạy Baseline Chatbot qua toàn bộ test cases để lộ rõ hạn chế
    # của Chatbot Cấp 2 (không tra được hạn mức & ngân sách nội bộ).
    print("\n--- DEMO MỐC 2: CHATBOT BASELINE (KHÔNG CÓ TOOL) ---")

    for case in tests:
        print(f"\n=== Test Case #{case['id']} | {case['category']} ===")
        print(f"🎯 Kỳ vọng: {case['expected_behavior']}")
        run_baseline_chatbot(case["question"], provider)

    print("\n--- DEMO MỐC 3: REACT AGENT (SẼ LẮP Ở MỐC 3) ---")
    run_react_agent(tests[2]["question"], provider)
