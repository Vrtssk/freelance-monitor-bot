import logging

from filters.keywords import match_keywords
from filters.llm import LLMClassifier
from filters.vacancy import is_vacancy
from models.schemas import JobPosting

logger = logging.getLogger(__name__)


class HybridFilter:
    """
    Hybrid filter pipeline:
    1) Keyword pre-filter (fast, free)
    2) LLM classification for candidates (OpenRouter / DeepSeek)
    """

    def __init__(self) -> None:
        self.llm = LLMClassifier()

    async def filter_posts(
        self,
        posts: list[JobPosting],
        user_topics: set[str],
    ) -> list[JobPosting]:
        if not user_topics:
            return []

        results: list[JobPosting] = []
        for post in posts:
            # Hard exclude: job vacancies / hiring are never relevant to a
            # freelance-order monitor (user wants one-off orders or long-term
            # collaboration, not "приём на работу").
            if is_vacancy(post):
                logger.debug("Vacancy skipped: %s — %s", post.title[:60], post.url)
                continue

            matched = match_keywords(post, user_topics)
            if not matched:
                continue

            if self.llm.enabled:
                relevant, llm_topics, reason = await self.llm.classify(post, user_topics)
                if reason.startswith("llm_error") or reason == "llm_disabled":
                    # LLM unavailable — fall back to keyword matches
                    post.matched_topics = matched
                    post.match_reason = "keywords (llm unavailable)"
                    results.append(post)
                elif relevant:
                    post.matched_topics = llm_topics or matched
                    post.match_reason = reason or "llm"
                    results.append(post)
                else:
                    logger.debug("LLM rejected: %s — %s", post.title[:60], reason)
            else:
                post.matched_topics = matched
                post.match_reason = "keywords"
                results.append(post)
        return results
