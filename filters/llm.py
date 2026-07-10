import json
import logging
import re

from openai import AsyncOpenAI

from config.settings import settings
from config.topics import TOPICS
from models.schemas import JobPosting

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — классификатор фриланс-объявлений на русском языке.
Определи, относится ли объявление к одной или нескольким из категорий:

- frontend: Front-end (React, Vue, Angular, JS/TS, SPA)
- markup: Верстка сайтов (HTML/CSS, лендинги, Figma→HTML)
- parsing: Парсинг и сбор данных (scraper, сбор данных)
- scripts: Скрипты и автоматизация (скрипты, cron, selenium, автоматизация)
- chatbots: Чат-боты (Telegram/Discord боты, chatbot)

Ответь ТОЛЬКО валидным JSON без markdown:
{"relevant": true/false, "subtopics": ["frontend"], "reason": "кратко почему"}

Если объявление не по IT-разработке или не по этим темам — relevant=false, subtopics=[].
"""


class LLMClassifier:
    """Classify job postings via OpenRouter-compatible OpenAI API."""

    def __init__(self) -> None:
        self.enabled = settings.LLM_ENABLED and bool(settings.LLM_API_KEY)
        self.client: AsyncOpenAI | None = None
        if self.enabled:
            self.client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
            )

    async def classify(
        self,
        post: JobPosting,
        allowed_topics: set[str] | None = None,
    ) -> tuple[bool, list[str], str]:
        """
        Returns (relevant, topic_keys, reason).
        If LLM disabled or fails, falls back to keyword-only already done upstream.
        """
        if not self.enabled or not self.client:
            return False, [], "llm_disabled"

        topics_desc = ", ".join(f"{t['key']}={t['emoji']} {t['name']}" for t in TOPICS)
        user_content = (
            f"Доступные категории: {topics_desc}\n\n"
            f"Заголовок: {post.title}\n"
            f"Бюджет: {post.budget or '—'}\n"
            f"Категория: {post.category or '—'}\n"
            f"Описание: {(post.description or '')[:1200]}\n"
        )
        if allowed_topics:
            user_content += f"\nИнтересующие пользователя темы: {', '.join(sorted(allowed_topics))}\n"

        try:
            resp = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
                max_tokens=300,
            )
            raw = (resp.choices[0].message.content or "").strip()
            data = self._parse_json(raw)
            relevant = bool(data.get("relevant"))
            subtopics = [s for s in (data.get("subtopics") or []) if isinstance(s, str)]
            if allowed_topics:
                subtopics = [s for s in subtopics if s in allowed_topics]
            reason = str(data.get("reason") or "")[:300]
            if relevant and not subtopics and allowed_topics:
                relevant = False
            return relevant, subtopics, reason
        except Exception as exc:
            logger.warning("LLM classify failed: %s", exc)
            return False, [], f"llm_error: {exc}"

    def _parse_json(self, raw: str) -> dict:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", raw, re.S)
            if m:
                return json.loads(m.group(0))
            raise
