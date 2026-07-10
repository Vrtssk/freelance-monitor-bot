from config.topics import SOURCES, TOPIC_BY_KEY
from models.schemas import JobPosting


def format_job_notification(post: JobPosting) -> str:
    """Format a real JobPosting as Telegram HTML notification."""
    topics_label = "—"
    if post.matched_topics:
        parts = []
        for key in post.matched_topics:
            t = TOPIC_BY_KEY.get(key)
            if t:
                parts.append(f"{t['emoji']} {t['name']}")
            else:
                parts.append(key)
        topics_label = ", ".join(parts)

    src = SOURCES.get(post.source, {})
    src_emoji = src.get("emoji", "")
    src_name = src.get("name", post.source)
    budget = post.budget or "Не указан"
    desc = (post.description or "").strip()
    if len(desc) > 600:
        desc = desc[:600].rsplit(" ", 1)[0] + "…"

    lines = [
        "🆕 <b>Новое объявление</b>",
        "",
        f"<b>{_escape(post.title)}</b>",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"🏷 <b>Тема:</b> {topics_label}",
        f"💰 <b>Бюджет:</b> {_escape(budget)}",
        f"📍 <b>Источник:</b> {src_emoji} {src_name}",
    ]
    if post.match_reason and post.match_reason not in ("keywords", "llm"):
        lines.append(f"💡 <i>{_escape(post.match_reason)}</i>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    if desc:
        lines.extend(["", _escape(desc)])
    lines.extend(["", f'🔗 <a href="{post.url}">Открыть на {src_name}</a>'])
    return "\n".join(lines)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
