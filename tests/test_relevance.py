"""Tests for relevance scoring, complexity heuristic, price parsing and the
scraper signal extractors (used by the Топ-5 feature)."""
from datetime import datetime, timezone

from scrapers.base import parse_relative_time, parse_responses
from utils.relevance import (
    age_hours_from,
    compute_relevance,
    estimate_complexity,
    parse_price,
)


# --- complexity heuristic -------------------------------------------------


def test_complexity_simple_is_low():
    assert estimate_complexity("Нужна простая вёрстка одностраничного лендинга") <= 2


def test_complexity_complex_is_high():
    c = estimate_complexity(
        "Микросервисы, архитектура, интеграция с CRM и базой данных, ML-модель"
    )
    assert c >= 4


def test_complexity_none_defaults_to_3():
    assert estimate_complexity(None) == 3


# --- price parsing --------------------------------------------------------


def test_parse_price_rub():
    assert parse_price("10 000 ₽") == 10000
    assert parse_price("35 000 руб") == 35000


def test_parse_price_usd_converted():
    assert parse_price("$500") == 45000


def test_parse_price_negotiated_is_none():
    assert parse_price("Обсуждается") is None
    assert parse_price("договорная") is None
    assert parse_price(None) is None


# --- relevance formula ----------------------------------------------------


def test_zero_responses_complex_beats_many_responses_simple():
    # Per spec: 0 responses + complexity 3/5 must outrank 20 responses + 1/5.
    fresh = dict(age_hours=1, price=10000)
    a = compute_relevance(responses=0, complexity=3, **fresh)
    b = compute_relevance(responses=20, complexity=1, **fresh)
    assert a > b


def test_responses_dominates():
    assert compute_relevance(responses=0) > compute_relevance(responses=20)


def test_lower_complexity_is_more_relevant():
    assert compute_relevance(complexity=1) > compute_relevance(complexity=5)


def test_fresher_is_more_relevant():
    assert compute_relevance(age_hours=0) > compute_relevance(age_hours=48)


# --- recency proxy --------------------------------------------------------


def test_age_from_published():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    pub = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)  # 12h earlier
    assert 11.9 < age_hours_from(now, pub, None) < 12.1


def test_age_falls_back_to_seen():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    seen = datetime(2025, 12, 31, 12, 0, tzinfo=timezone.utc)  # 24h earlier
    assert 23.9 < age_hours_from(now, None, seen) < 24.1


def test_age_none_is_zero():
    assert age_hours_from(datetime.now(timezone.utc), None, None) == 0.0


# --- scraper signal extractors -------------------------------------------


def test_parse_relative_time():
    now = datetime.now(timezone.utc)
    assert parse_relative_time("сегодня") is not None
    assert parse_relative_time("вчера") is not None
    assert parse_relative_time("") is None
    dt = parse_relative_time("2 часа назад")
    age = (now - dt).total_seconds() / 3600
    assert 1.9 < age < 2.1


def test_parse_responses():
    assert parse_responses("5 предложений по цене") == 5
    assert parse_responses("12 откликов") == 12
    assert parse_responses("без откликов") == 0
    assert parse_responses("") == 0
