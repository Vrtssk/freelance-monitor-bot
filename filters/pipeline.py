import logging

from filters.keywords import match_keywords
from filters.llm import LLMClassifier
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
            matched = match_keywords(post, user_topics)
            if not matched:
                continue

            if self.llm.enabled:
                relevant, llm_topics, reason = await self.llm.classify(post, user_topics)
                if not relevant:
                    logger.debug("LLM rejected: %s — %s", post.title[:60], reason)
                    continue
                post.matched_topics = llm_topics or matched
                post.match_reason = reason or "llm"
            else:
                post.matched_topics = matched
                post.match_reason = "keywords"
            results.append(post)
        return results
