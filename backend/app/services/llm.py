from __future__ import annotations

import httpx

from app.core.config import settings


class OpenRouterService:
    def __init__(self) -> None:
        self.base_url = settings.openrouter_base_url.rstrip("/")

    def _build_messages(self, query: str, context_blocks: list[str]) -> list[dict[str, str]]:
        context = "\n\n".join(context_blocks)
        system_prompt = (
            "Ban la tro ly tu van tuyen sinh dai hoc. "
            "Chi duoc tra loi dua tren context duoc cung cap. "
            "Neu context khong du, phai noi ro 'khong du du lieu trong bo crawl hien tai'. "
            "Khong duoc bịa, khong suy doan, khong dua URL."
        )
        user_prompt = (
            f"Cau hoi nguoi dung: {query}\n\n"
            "Context truy xuat:\n"
            f"{context}\n\n"
            "Yeu cau tra loi ngan gon, dung trong pham vi du lieu."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def generate(self, query: str, context_blocks: list[str]) -> str:
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is missing")

        payload = {
            "model": settings.openrouter_model,
            "messages": self._build_messages(query=query, context_blocks=context_blocks),
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
