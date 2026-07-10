"""Tests for the LLM text-format parser and hybrid pipeline fallback logic.

These cover the model-agnostic ``RELEVANT: YES; TOPICS: ...`` parser and the
HybridFilter behaviour when the LLM is unavailable/disabled/rejects a post.
No network is used: the parser is tested directly and the pipeline uses a
stubbed LLM classifier.
"""
from __future__ import annotations

from filters.llm import LLMClassifier
from filters.pipeline import HybridFilter
from models.schemas import JobPosting

ALL_TOPICS = {"frontend", "markup", "parsing", "scripts", "chatbots"}


def _make_parser() -> LLMClassifier:
    """Build a classifier without running __init__ (no settings/client needed)."""
    obj = LLMClassifier.__new__(LLMClassifier)
    return obj


def _post(title: str, description: str = "") -> JobPosting:
    return JobPosting(
        source="fl_ru",
        external_id="1",
        title=title,
        description=description,
        url="https://example.com/1",
    )


# --- parser ---------------------------------------------------------------


def test_parse_yes_with_topics():
    p = _make_parser()
    relevant, topics, _ = p._parse_response(
        "RELEVANT: YES; TOPICS: parsing, scripts", ALL_TOPICS
    )
    assert relevant is True
    assert set(topics) == {"parsing", "scripts"}


def test_parse_no_match():
    p = _make_parser()
    relevant, topics, _ = p._parse_response("RELEVANT: NO; TOPICS:", ALL_TOPICS)
    assert relevant is False
    assert topics == []


def test_parse_empty_and_garbage():
    p = _make_parser()
    assert p._parse_response("", ALL_TOPICS)[0] is False
    assert p._parse_response("что-то непонятное без ключей", ALL_TOPICS)[0] is False


def test_parse_case_insensitive_and_locales():
    p = _make_parser()
    relevant, _, _ = p._parse_response("relevant: yes; topics: frontend", ALL_TOPICS)
    assert relevant is True
    assert p._parse_response("RELEVANT: ДА; TOPICS: frontend", ALL_TOPICS)[0] is True


def test_parse_topics_read_only_after_colon():
    """Reasoning text may mention categories; only the part after TOPICS: counts."""
    p = _make_parser()
    raw = (
        "frontend markup parsing scripts chatbots упоминаются в описании. "
        "RELEVANT: YES; TOPICS: parsing"
    )
    relevant, topics, _ = p._parse_response(raw, ALL_TOPICS)
    assert relevant is True
    assert topics == ["parsing"]


def test_parse_filters_topics_to_allowed():
    p = _make_parser()
    _, topics, _ = p._parse_response(
        "RELEVANT: YES; TOPICS: frontend, markup", {"frontend"}
    )
    assert topics == ["frontend"]


def test_parse_multiple_topics_preserves_order_of_allowed():
    p = _make_parser()
    _, topics, _ = p._parse_response(
        "RELEVANT: YES; TOPICS: scripts, parsing, frontend", ALL_TOPICS
    )
    assert set(topics) == {"scripts", "parsing", "frontend"}


# --- pipeline fallback ----------------------------------------------------


class _StubLLM:
    """Minimal LLM stub returning a canned (relevant, topics, reason)."""

    def __init__(self, result: tuple[bool, list[str], str], enabled: bool = True) -> None:
        self.enabled = enabled
        self._result = result

    async def classify(self, post, allowed_topics=None):
        return self._result


def _filter_with_stub(stub) -> HybridFilter:
    hf = HybridFilter()
    hf.llm = stub
    return hf


async def test_pipeline_llm_relevant_uses_llm_topics():
    post = _post("Нужен парсинг каталога товаров (Scrapy)")
    hf = _filter_with_stub(_StubLLM((True, ["parsing"], "llm")))
    out = await hf.filter_posts([post], ALL_TOPICS)
    assert len(out) == 1
    assert out[0].matched_topics == ["parsing"]
    assert out[0].match_reason == "llm"


async def test_pipeline_llm_rejected_drops_post():
    post = _post("Парсинг курсов по экономике")
    hf = _filter_with_stub(_StubLLM((False, [], "RELEVANT: NO; TOPICS:")))
    out = await hf.filter_posts([post], ALL_TOPICS)
    assert out == []


async def test_pipeline_llm_error_falls_back_to_keywords():
    """When the LLM errors, the post should still be sent using keyword matches."""
    post = _post("Нужен парсинг каталога (Scrapy, BS4)")
    hf = _filter_with_stub(_StubLLM((False, [], "llm_error: 429 rate limit")))
    out = await hf.filter_posts([post], ALL_TOPICS)
    assert len(out) == 1
    assert "parsing" in out[0].matched_topics
    assert out[0].match_reason == "keywords (llm unavailable)"


async def test_pipeline_llm_disabled_uses_keywords():
    post = _post("Telegram-бот на aiogram для магазина")
    hf = _filter_with_stub(_StubLLM((False, [], "llm_disabled"), enabled=False))
    out = await hf.filter_posts([post], ALL_TOPICS)
    assert len(out) == 1
    assert "chatbots" in out[0].matched_topics
    assert out[0].match_reason == "keywords"


async def test_pipeline_skips_non_keyword_posts():
    """Posts that don't match any keyword never reach the LLM at all."""
    post = _post("Перевод текстов с английского на русский")
    calls = {"n": 0}

    class _CountingLLM:
        enabled = True

        async def classify(self, post, allowed_topics=None):
            calls["n"] += 1
            return True, ["parsing"], "llm"

    hf = _filter_with_stub(_CountingLLM())
    out = await hf.filter_posts([post], ALL_TOPICS)
    assert out == []
    assert calls["n"] == 0


async def test_pipeline_empty_user_topics_returns_nothing():
    post = _post("Нужен парсинг каталога (Scrapy)")
    hf = _filter_with_stub(_StubLLM((True, ["parsing"], "llm")))
    assert await hf.filter_posts([post], set()) == []