import logging
import re

from openai import AsyncOpenAI

from config.settings import settings
from config.topics import TOPICS
from models.schemas import JobPosting

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — классификатор фриланс-объявлений. Категории IT-разработки:
frontend, markup, parsing, scripts, chatbots.
Ответь ОДНОЙ строкой без пояснений, строго в формате:
RELEVANT: YES|NO; TOPICS: <список через запятую из допустимых категорий, или пусто>
Пример: RELEVANT: YES; TOPICS: chatbots, parsing
Если объявление не по IT-разработке — RELEVANT: NO; TOPICS:"""


class LLMClassifier:
    """Classify job postings via OpenRouter-compatible OpenAI API."""

    def __init__(self) -> None:
        self.enabled = settings.LLM_ENABLED and bool(settings.LLM_API_KEY)
        self.client: AsyncOpenAI | None = None
        if self.enabled:
            self.client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                timeout=30,
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
            msg = resp.choices[0].message
            # Prefer final `content`; some reasoning models leave it empty and
            # put the answer in `reasoning`. Use reasoning only as fallback.
            raw = (msg.content or "").strip() or (
                getattr(msg, "reasoning", "") or ""
            ).strip()
            relevant, subtopics, reason = self._parse_response(raw, allowed_topics)
            if relevant and not subtopics and allowed_topics:
                relevant = False
            return relevant, subtopics, reason
        except Exception as exc:
            logger.warning("LLM classify failed: %s", exc)
            return False, [], f"llm_error: {exc}"

    def _parse_response(self, raw: str, allowed_topics: set[str]) -> tuple[bool, list[str], str]:
        """
        Parse a simple 'RELEVANT: YES; TOPICS: a, b' answer (model-agnostic).
        Topics are read only from the portion after 'TOPICS:' so that category
        names mentioned elsewhere in a reasoning trace don't cause false hits.
        """
        low = raw.lower()
        relevant = bool(re.search(r"relevant\s*[:=]\s*(yes|true|да|1)", low))
        topics_part = ""
        tm = re.search(r"topics?\s*[:=]\s*(.+?)(?:\n|$)", low)
        if tm:
            topics_part = tm.group(1)
        topics: list[str] = [k for k in allowed_topics if k.lower() in topics_part]
        reason = raw[:300] if raw else "llm"
        return relevant, topics, reason
