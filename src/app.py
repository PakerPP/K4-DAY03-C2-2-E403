"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.

Chủ đề nhóm: TRỢ LÝ DUYỆT CHI PHÍ DOANH NGHIỆP (Expense Approval Agent)
Trạng thái: Mốc 3 - Baseline Chatbot + ReAct Agent Loop có Guardrails.
"""

import json
import os
import re
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


def parse_llm_output(text: str) -> dict:
    """
    Bóc tách output của LLM thành các thành phần ReAct.

    LLM đôi khi tự "diễn" luôn cả Observation. Ta cắt bỏ phần đó để đảm bảo
    Observation CHỈ đến từ tool thật (Guardrail chống bịa dữ liệu - quy tắc 2
    trong REACT_SYSTEM_PROMPT của Role 3).

    Returns:
        dict: {"thought": str, "action": str, "action_input": str, "final": str}
    """
    # Cắt bỏ mọi thứ LLM tự bịa từ "Observation:" trở đi
    cut = re.split(r"^\s*Observation\s*:", text, maxsplit=1, flags=re.M | re.I)[0]

    def grab(pattern, source=cut):
        m = re.search(pattern, source, flags=re.M | re.I)
        return m.group(1).strip() if m else ""

    return {
        "thought": grab(r"^\s*Thought\s*:\s*(.+?)\s*$"),
        "action": grab(r"^\s*Action\s*:\s*(.+?)\s*$"),
        # Action Input có thể trải nhiều dòng (JSON xuống dòng)
        "action_input": grab(r"^\s*Action\s*Input\s*:\s*(.*?)(?=^\s*(?:Thought|Action|Final Answer)\s*:|\Z)"),
        "final": grab(r"^\s*Final\s*Answer\s*:\s*(.*?)(?=^\s*(?:Thought|Action)\s*:|\Z)"),
    }


def parse_action_input(raw: str):
    """
    Chuyển Action Input (chuỗi) thành dict tham số cho tool.

    Chấp nhận cả trường hợp LLM bọc JSON trong ```json ... ``` .

    Returns:
        tuple[dict | None, str]: (tham số, thông báo lỗi nếu có)
    """
    if not raw:
        return {}, ""

    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()

    # Chỉ lấy phần từ dấu { đầu tiên tới dấu } cuối cùng
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return None, f"Action Input không phải JSON hợp lệ ({e.msg})."

    if not isinstance(data, dict):
        return None, "Action Input phải là một đối tượng JSON (dạng {\"key\": value})."

    return data, ""


def execute_tool(tool_name: str, tool_args: dict) -> str:
    """
    Gọi tool thật từ AVAILABLE_TOOLS (Role 2) một cách an toàn.

    Mọi lỗi đều được chuyển thành chuỗi Observation để Agent tự xử lý,
    tuyệt đối không để exception làm chết vòng lặp.
    """
    if tool_name not in AVAILABLE_TOOLS:
        ds = ", ".join(AVAILABLE_TOOLS.keys())
        return f"LỖI: Không tồn tại tool '{tool_name}'. Các tool hợp lệ: {ds}."

    try:
        return AVAILABLE_TOOLS[tool_name](**tool_args)
    except TypeError as e:
        return f"LỖI: Sai tham số khi gọi '{tool_name}' ({e})."
    except Exception as e:
        return f"LỖI: Tool '{tool_name}' gặp sự cố ({type(e).__name__}: {e})."


def run_react_agent(user_query: str, provider) -> str:
    """
    Vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.

    Guardrails được cài đặt:
        1. MAX_ITERATIONS - chặn vòng lặp vô hạn (Role 3 đặt = 5).
        2. Chống lặp - phát hiện Agent gọi lại y hệt Action + Input trước đó.
        3. Tool không tồn tại / sai tham số -> trả Observation lỗi, không crash.
        4. Observation do LLM tự bịa bị cắt bỏ trước khi ghép vào scratchpad.
        5. Hết lượt -> trả lời an toàn thay vì tự bịa quyết định duyệt.

    Returns:
        str: Final Answer của Agent (hoặc thông báo dừng an toàn).
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    if not REACT_PROMPT_READY:
        msg = (
            "⏳ ReAct Agent chưa sẵn sàng: prompts.py chưa có "
            "REACT_SYSTEM_PROMPT / MAX_ITERATIONS (Role 3)."
        )
        print(msg)
        return msg

    scratchpad = ""       # Nhật ký Thought/Action/Observation tích lũy
    seen_actions = set()  # Guardrail 2: nhớ các cặp (tool, input) đã gọi

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        prompt = f"Câu hỏi của người dùng: {user_query}\n"
        if scratchpad:
            prompt += f"\nNhật ký các bước đã thực hiện:\n{scratchpad}"
        prompt += "\nHãy tiếp tục theo đúng định dạng ReAct."

        try:
            raw = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        except Exception as e:
            msg = f"❌ Lỗi gọi LLM ở step {step}: {e}"
            print(msg)
            return msg

        parsed = parse_llm_output(raw)

        if parsed["thought"]:
            print(f"🧠 Thought: {parsed['thought']}")

        # Agent đã đủ dữ liệu để kết luận
        if parsed["final"]:
            print(f"🏁 Final Answer: {parsed['final']}")
            return parsed["final"]

        # Không có Action mà cũng không có Final Answer -> output sai định dạng
        if not parsed["action"]:
            print("⚠️ GUARDRAIL: LLM trả về sai định dạng ReAct. Nhắc lại yêu cầu.")
            scratchpad += (
                "\nObservation: LỖI ĐỊNH DẠNG - bạn phải trả lời theo đúng mẫu "
                "'Thought/Action/Action Input' hoặc 'Final Answer'.\n"
            )
            continue

        tool_name = parsed["action"].strip().strip("`'\"[]()")
        tool_args, err = parse_action_input(parsed["action_input"])

        print(f"🛠️ Action: {tool_name}")
        print(f"📥 Action Input: {parsed['action_input'] or '{}'}")

        if err or tool_args is None:
            observation = f"LỖI: {err}"
        else:
            # Guardrail 2: chống gọi lặp lại y hệt
            signature = f"{tool_name}|{json.dumps(tool_args, sort_keys=True, ensure_ascii=False)}"
            if signature in seen_actions:
                print("🛡️ GUARDRAIL: Phát hiện gọi lặp lại cùng Action + Input.")
                observation = (
                    "LỖI: Bạn vừa gọi lại đúng tool này với đúng tham số cũ. "
                    "Kết quả không đổi. Hãy đổi hướng hoặc đưa ra Final Answer."
                )
            else:
                seen_actions.add(signature)
                observation = execute_tool(tool_name, tool_args)

        print(f"👁️ Observation: {observation}")

        scratchpad += (
            f"\nThought: {parsed['thought']}"
            f"\nAction: {tool_name}"
            f"\nAction Input: {parsed['action_input']}"
            f"\nObservation: {observation}\n"
        )

    # Guardrail 1 & 5: hết lượt mà chưa kết luận -> dừng an toàn
    msg = (
        f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn {MAX_ITERATIONS} bước "
        f"nhưng chưa đủ dữ liệu để kết luận. Agent dừng an toàn và KHÔNG tự "
        f"quyết định duyệt. Đề nghị chuyển hồ sơ cho bộ phận Tài chính - Kế toán."
    )
    print(f"\n{msg}")
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

    # Chạy song song 2 hệ thống trên cùng bộ test case để Role 5 so sánh:
    # Chatbot Cấp 2 (không tool) vs ReAct Agent Cấp 3 (có tool + guardrails).
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    for case in tests:
        print("\n" + "=" * 60)
        print(f"=== Test Case #{case['id']} | {case['category']} ===")
        print(f"🎯 Kỳ vọng: {case['expected_behavior']}")
        print("=" * 60)

        if mode in ("all", "baseline"):
            run_baseline_chatbot(case["question"], provider)

        if mode in ("all", "react"):
            run_react_agent(case["question"], provider)

    print("\n✅ Hoàn tất. Dùng 'python src/app.py react' để chỉ chạy ReAct Agent.")
