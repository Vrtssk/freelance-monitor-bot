import re

from models.schemas import JobPosting

# Strong hiring / vacancy (найм) markers. A post is treated as a job vacancy
# (permanent hire, interview, full-time role) — and therefore NOT relevant to a
# freelance-order monitor — when ANY of these patterns match. We deliberately
# favour recall here: the user never wants "приём на работу", only one-off
# orders or long-term collaboration.
_VACANCY_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"собеседован",            # собеседование / по результатам собеседования
        r"ваканси",               # вакансия / вакансий
        r"трудоустро",            # трудоустройство / официальное трудоустройство
        r"полная занятост",
        r"неполная занятост",
        r"частичная занятост",
        r"график работ",           # график работы
        r"гибкий график",
        r"сменный график",
        r"оклад",
        r"заработная плата",
        r"з/п\b",
        r"\bв штат",              # ищем в штат / берём в штат
        r"на постоянную работу",
        r"постоянную работу",
        r"при[её]м на работу",
        r"полный день",
    ]
]


def is_vacancy(post: JobPosting) -> bool:
    """Return True if the posting is a job vacancy / hiring rather than a
    freelance order or long-term collaboration.

    Detection is text-based (title + description + category) so it works across
    all scraped sources without source-specific parsing.
    """
    text = post.text_for_filter
    if not text:
        return False
    return any(p.search(text) for p in _VACANCY_PATTERNS)
