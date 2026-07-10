"""Relevance ranking for the "Топ-5 актуальных" feature.

A posting is more relevant when it is:
1. Fresh and has few responses (less competition) — the strongest factor.
2. Simpler (lower estimated complexity).
3. Higher priced — minimal weight, kept for future tuning.

The score is a float in [0, 1]; higher = more relevant.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

# Weights (sum to 1). Responses dominate, then complexity, then recency,
# then price (minimal, per spec).
W_RESPONSES = 0.55
W_COMPLEXITY = 0.20
W_RECENCY = 0.18
W_PRICE = 0.07

# Complexity heuristic: simple vs complex keyword groups.
_SIMPLE_KW = [
    "прост", "лендинг", "верстка", "одностраничн", "скрипт", "небольш",
    "минимальн", "типов", "шаблон", "конверси", "копирайт",
]
_COMPLEX_KW = [
    "микросервис", "архитектур", "распределённ", "высоконагруж", "база данных",
    "бд ", " бд", "ml", "нейросет", "интеграци", "api", "crm", "erp",
    "платёж", "платежн", "безопасност", "крипт", "блокчейн", "админк",
    "дашборд", "кластер", "kubernet", "масштабир", "рефакторинг",
    "оптимизаци", "машинное обучен", "нейро",
]


def estimate_complexity(description: str | None) -> int:
    """Estimate project complexity on a 1..5 scale from the description text.

    1 = trivial (e.g. a landing page), 5 = hard (e.g. microservices + ML).
    """
    if not description:
        return 3
    text = description.lower()
    score = 3
    for kw in _SIMPLE_KW:
        if kw in text:
            score -= 1
    for kw in _COMPLEX_KW:
        if kw in text:
            score += 1
    # Longer descriptions tend to describe bigger scopes.
    length = len(description)
    if length > 1200:
        score += 1
    elif length < 200:
        score -= 1
    return max(1, min(5, score))


_PRICE_RE = re.compile(r"(\d[\d\s]*)(?:\s*(?:₽|руб|rub|rur))?|\$\s*(\d[\d\s]*)", re.I)


def parse_price(budget: str | None) -> Optional[int]:
    """Extract a numeric price (in RUB) from a budget string, or None."""
    if not budget:
        return None
    low = budget.lower()
    if any(w in low for w in ("обсужда", "договор", "индивидуальн", "по запрос")):
        return None
    m = _PRICE_RE.search(budget)
    if not m:
        return None
    raw = (m.group(1) or m.group(2) or "").replace(" ", "")
    if not raw.isdigit():
        return None
    value = int(raw)
    if m.group(2):  # USD
        value = int(value * 90)
    return value


def _responses_score(responses: int) -> float:
    # 0 responses -> 1.0; 20 responses -> ~0.25; decays gently.
    return 1.0 / (1.0 + 0.15 * max(0, responses))


def _complexity_score(complexity: int) -> float:
    # lower complexity -> higher score (1 -> 1.0, 5 -> 0.2).
    c = max(1, min(5, complexity))
    return (6 - c) / 5.0


def _recency_score(age_hours: float) -> float:
    # fresh -> 1.0; ~12h half-life.
    return 1.0 / (1.0 + max(0.0, age_hours) / 12.0)


def _price_score(price: Optional[float]) -> float:
    if not price:
        return 0.5
    # mild positive slope, saturated at 100k RUB.
    return 0.5 + 0.5 * min(price / 100_000.0, 1.0)


def compute_relevance(
    *,
    responses: int = 0,
    age_hours: float = 0.0,
    complexity: int = 3,
    price: Optional[float] = None,
) -> float:
    """Return a relevance score in [0, 1] (higher = more relevant)."""
    return (
        W_RESPONSES * _responses_score(responses)
        + W_COMPLEXITY * _complexity_score(complexity)
        + W_RECENCY * _recency_score(age_hours)
        + W_PRICE * _price_score(price)
    )


def age_hours_from(
    now: datetime, published_at: Optional[datetime], seen_at: Optional[datetime]
) -> float:
    """Recency proxy: prefer the real publish date, fall back to first-seen."""
    base = published_at or seen_at
    if not base:
        return 0.0
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return max(0.0, (now - base).total_seconds() / 3600.0)