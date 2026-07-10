import re

from config.topics import SOURCES, TOPIC_BY_KEY
from models.schemas import JobPosting

# UI text leaked from exchange pages (e.g. Kwork's "Показать полностью" button).
_SCRAPER_ARTIFACTS = [
    "показать полностью",
    "показать ещё",
    "показать больше",
    "читать далее",
    "читать полностью",
    "show full",
    "read more",
]

_DESC_MAX = 500


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _dedupe_repeated(text: str) -> str:
    """Some exchanges (Kwork) embed a truncated preview ending in '…'/'...'
    immediately followed by the full text, so the body repeats. Keep only the
    preview copy when the text after the ellipsis restarts with the same lead."""
    if "…" in text:
        sep, sep_len = "…", 1
    elif "..." in text:
        sep, sep_len = "...", 3
    else:
        return text
    idx = text.find(sep)
    if idx < 20:
        return text
    head = text[:idx].rstrip(" .,-")
    if len(head) < 20:
        return text
    tail = text[idx + sep_len:].lstrip(" .,-")
    if tail.startswith(head[:20]):
        return head
    return text


def _clean_description(text: str, title: str) -> str:
    """Strip scraper noise: a duplicated title prefix and UI 'show full' junk."""
    if not text:
        return ""
    # Kwork embeds the title at the start of the description block.
    if title and text.lower().startswith(title.lower()):
        text = text[len(title):].lstrip(" \n\t—-")
    for art in _SCRAPER_ARTIFACTS:
        text = re.sub(rf"\s*{re.escape(art)}\s*", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    # Drop a stray ellipsis left behind by a "show full" truncation.
    text = text.strip(" …")
    return _dedupe_repeated(text)


def _truncate(text: str, limit: int = _DESC_MAX) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:") + "…"


def _topics_label(keys: list[str]) -> str:
    parts = []
    for key in keys:
        topic = TOPIC_BY_KEY.get(key)
        parts.append(f"{topic['emoji']} {topic['name']}" if topic else key)
    return ", ".join(parts)


def _topics_labels_from_csv(csv: str | None) -> str:
    if not csv:
        return ""
    return _topics_label([k for k in csv.split(",") if k])


def format_top_list(items: list[tuple]) -> str:
    """Render the ranked top-N relevant postings as one compact message.

    ``items`` is a list of (SeenPost row, score in [0, 1]).
    """
    if not items:
        return "🔥 Пока нет подходящих объявлений по твоим темам."
    lines = ["🔥 <b>Топ-5 актуальных объявлений</b>", ""]
    for i, (row, score) in enumerate(items, 1):
        src = SOURCES.get(row.source, {})
        src_emoji = src.get("emoji", "")
        src_name = src.get("name", row.source)
        topics = _topics_labels_from_csv(row.matched_topics)
        budget = row.budget or "Не указан"
        pct = int(score * 100)
        title = _escape(row.title or "")
        lines.append(f"{i}. {topics}")
        lines.append(f"<b>{title}</b> · 💰 {_escape(budget)} · {src_emoji} {src_name}")
        lines.append(
            f"🔗 <a href=\"{row.url}\">открыть на {src_name}</a> · "
            f"релевантность {pct}%"
        )
        lines.append("")
    return "\n".join(lines).strip()


def format_recent_list(rows: list) -> str:
    """Render the most recently seen postings as one compact message.

    ``rows`` is a list of SeenPost rows ordered newest-first. Unlike the
    relevance-ranked top list, this is a raw, topic-agnostic feed.
    """
    if not rows:
        return "📋 Пока нет сохранённых объявлений."
    lines = ["📋 <b>Последние 10 объявлений</b>", ""]
    for i, row in enumerate(rows, 1):
        src = SOURCES.get(row.source, {})
        src_emoji = src.get("emoji", "")
        src_name = src.get("name", row.source)
        topics = _topics_labels_from_csv(row.matched_topics)
        budget = row.budget or "Не указан"
        title = _escape(row.title or "")
        lines.append(f"{i}. {topics}" if topics else f"{i}.")
        lines.append(f"<b>{title}</b> · 💰 {_escape(budget)} · {src_emoji} {src_name}")
        lines.append(f'🔗 <a href="{row.url}">открыть на {src_name}</a>')
        lines.append("")
    return "\n".join(lines).strip()


def format_job_notification(post: JobPosting) -> str:
    """Render a JobPosting as a clean, minimal Telegram HTML notification."""
    title = _escape(post.title)
    topics = _topics_label(post.matched_topics)

    budget = post.budget or "Не указан"
    src = SOURCES.get(post.source, {})
    src_emoji = src.get("emoji", "")
    src_name = src.get("name", post.source)

    cleaned = _clean_description(post.description or "", post.title)
    desc = _escape(_truncate(cleaned)) if cleaned else ""

    lines = [f"🆕 <b>{title}</b>"]
    if topics:
        lines.append(topics)
    lines.append(f"💰 {_escape(budget)}  ·  {src_emoji} {src_name}")
    if desc:
        lines.append("")
        lines.append(desc)
    lines.append("")
    lines.append(f'🔗 <a href="{post.url}">{src_name}</a>')
    return "\n".join(lines)
