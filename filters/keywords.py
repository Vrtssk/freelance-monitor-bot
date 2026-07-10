from config.topics import TOPIC_BY_KEY, TOPICS
from models.schemas import JobPosting


def match_keywords(post: JobPosting, topic_keys: set[str] | None = None) -> list[str]:
    """
    Return topic keys that match the posting by keyword pre-filter.

    If topic_keys is None, check all known topics.
    """
    text = post.text_for_filter
    keys = topic_keys if topic_keys is not None else {t["key"] for t in TOPICS}
    matched: list[str] = []
    for key in keys:
        topic = TOPIC_BY_KEY.get(key)
        if not topic:
            continue
        for kw in topic["keywords"]:
            if kw.lower() in text:
                matched.append(key)
                break
    return matched


def any_keyword_hit(post: JobPosting, topic_keys: set[str] | None = None) -> bool:
    return bool(match_keywords(post, topic_keys))
