import os
from typing import Optional

# Try to load .env if available
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    def load_dotenv() -> None:  # fallback no-op
        return None

# Google Generative AI (Gemini)
import google.generativeai as genai

# Load .env if present
load_dotenv()

# Configure Gemini with API key from env
_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR-GEMINI-API-KEY-HERE")
if _API_KEY:
    genai.configure(api_key=_API_KEY)

# Use Gemini 2.5 model
_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

# Generation settings
_GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 2048,
}

_SYSTEM_PROMPT = (
    "Bạn là trợ lý AI thông minh và thân thiện. "
    "Hãy trả lời câu hỏi bằng tiếng Việt một cách tự nhiên và hữu ích. "
    "Nếu có nội dung ghi chú được cung cấp, hãy ưu tiên dựa vào đó để trả lời. "
    "Nếu không có nội dung ghi chú hoặc câu hỏi không liên quan, hãy trả lời như một trợ lý AI bình thường."
    "Nếu đi kèm lệnh Dịch, Giải thích, Tóm tắt thì trả lời như chatbot AI bình thường không cần dựa vào nội dung ghi chú"
)


def _truncate_context(text: str, max_chars: int = 8000) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    # Keep the beginning and the tail to retain context
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return head + "\n...\n" + tail


def ask_gemini(message: str, note_context: Optional[str] = None) -> str:
    """
    Call Gemini to answer a user message with optional note context.
    Returns plain text answer or a friendly error string.
    """
    if not _API_KEY:
        return "Chưa cấu hình GEMINI_API_KEY."

    try:
        # Try Gemini 2.5 models first, then fallback to older versions
        model_names = [
            "gemini-2.0-flash-exp",
            "gemini-exp-1206",
            "gemini-exp-1121",
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-pro"
        ]

        model = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                print(f"[DEBUG] Using model: {model_name}")
                break
            except Exception as e:
                print(f"[DEBUG] Model {model_name} failed: {e}")
                continue

        if not model:
            print("[DEBUG] All models failed, using fallback")
            model = genai.GenerativeModel("gemini-pro")

        # Tạo prompt có cấu trúc rõ ràng
        if note_context and note_context.strip():
            ctx = _truncate_context(note_context)
            full_prompt = f"""{_SYSTEM_PROMPT}

Nội dung ghi chú hiện tại:
---
{ctx}
---

Câu hỏi: {message}

Hãy trả lời dựa trên nội dung ghi chú nếu liên quan, hoặc trả lời như bình thường nếu không liên quan:"""
        else:
            full_prompt = f"""{_SYSTEM_PROMPT}

Câu hỏi: {message}

Hãy trả lời câu hỏi này:"""

        print(f"[DEBUG] Calling Gemini with prompt length: {len(full_prompt)}")

        resp = model.generate_content(
            full_prompt,
            generation_config=_GENERATION_CONFIG
        )

        if resp.text:
            print(f"[DEBUG] Gemini 2.5 responded successfully")
            return resp.text.strip()
        else:
            print(f"[DEBUG] Empty response from Gemini")
            return "Xin lỗi, tôi không thể tạo phản hồi phù hợp cho câu hỏi này."

    except Exception as e:
        error_msg = str(e)
        print(f"[DEBUG] Gemini error: {error_msg}")

        # Trả lời tự động cho một số câu hỏi cơ bản nếu API lỗi
        message_lower = message.lower()
        if any(greeting in message_lower for greeting in ['xin chào', 'chào', 'hi', 'hello']):
            return "Xin chào! Tôi là trợ lý AI của bạn. Bạn có câu hỏi gì không?"
        elif any(question in message_lower for question in ['bạn là ai', 'bạn là gì']):
            return "Tôi là trợ lý AI được tích hợp vào ứng dụng ghi chú này để giúp bạn trả lời câu hỏi."
        elif 'cảm ơn' in message_lower:
            return "Không có gì! Tôi luôn sẵn sàng giúp đỡ bạn."
        elif any(calc in message_lower for calc in ['tính', '+', '-', '*', '/', '=', 'bằng']):
            return "Tôi có thể giúp bạn tính toán! Hãy thử hỏi một phép tính đơn giản như '2 + 2 = ?'"
        else:
            return f"Hiện tại tôi gặp sự cố kỹ thuật với API Gemini 2.5. Tuy nhiên tôi vẫn có thể trả lời các câu hỏi cơ bản. Hãy thử hỏi 'hi' hoặc 'bạn là ai?'"
