from __future__ import annotations

import httpx

from app.core.config import settings


class OpenRouterService:
    def __init__(self) -> None:
        self.base_url = settings.openrouter_base_url.rstrip("/")

    def _build_messages(
        self,
        query: str,
        context_blocks: list[str],
        fallback_hint: str | None = None,
    ) -> list[dict[str, str]]:
        context = "\n\n".join(context_blocks)
        system_prompt = (
            "Bạn là trợ lý tư vấn tuyển sinh đại học. "
            "Chỉ được trả lời dựa trên context được cung cấp. "
            "Nếu context không đủ, trả lời lịch sự, tự nhiên, nêu rõ thiếu dữ liệu gì. "
            "Không được bịa, không suy đoán, không đưa URL, không hứa hẹn sẽ chủ động thông báo sau. "
            "Nếu có thể, gợi ý thông tin thay thế từ năm gần nhất có dữ liệu trong context."
        )
        hint_block = f"\n\nGợi ý fallback: {fallback_hint}" if fallback_hint else ""
        user_prompt = (
            f"Câu hỏi người dùng: {query}\n\n"
            "Context truy xuất:\n"
            f"{context}\n\n"
            f"Yêu cầu trả lời ngắn gọn, đúng trong phạm vi dữ liệu.{hint_block}"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def generate(self, query: str, context_blocks: list[str], fallback_hint: str | None = None) -> str:
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is missing")

        payload = {
            "model": settings.openrouter_model,
            "messages": self._build_messages(
                query=query,
                context_blocks=context_blocks,
                fallback_hint=fallback_hint,
            ),
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("OpenRouter returned empty choices")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise RuntimeError("OpenRouter returned empty content")
        return str(content).strip()


openrouter_service = OpenRouterService()
