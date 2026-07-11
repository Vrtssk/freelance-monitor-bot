from config.sources import ALL_SOURCE_KEYS, SCRAPE_SOURCES
from scrapers import get_all_scrapers, get_scrapers
from bot.keyboards import sources_kb


def test_sources_defined():
    assert len(SCRAPE_SOURCES) == 4
    assert set(ALL_SOURCE_KEYS) == {
        "fl_ru",
        "freelance_ru",
        "weblancer",
        "kwork",
    }


def test_get_scrapers_filters_by_enabled():
    enabled = {"fl_ru", "kwork"}
    scrapers = get_scrapers(enabled)
    assert [s.source for s in scrapers] == ["fl_ru", "kwork"]


def test_get_scrapers_none_returns_all():
    scrapers = get_scrapers(None)
    assert len(scrapers) == len(ALL_SOURCE_KEYS)
    assert [s.source for s in scrapers] == ALL_SOURCE_KEYS
    # get_all_scrapers is equivalent
    assert [s.source for s in get_all_scrapers()] == ALL_SOURCE_KEYS


def test_sources_kb_marks_enabled_and_disabled():
    disabled = {"fl_ru"}
    kb = sources_kb(disabled)
    labels = [b.text for row in kb.inline_keyboard for b in row]
    enabled_labels = [t for t in labels if t.startswith("✅")]
    disabled_labels = [t for t in labels if t.startswith("☐")]
    assert any("FL.ru" in t for t in disabled_labels)
    assert any("Kwork" in t for t in enabled_labels)
    # Back button present, toggles reference source keys
    assert any(b.callback_data == "menu:settings" for row in kb.inline_keyboard for b in row)
    assert any(b.callback_data == "src:toggle:fl_ru" for row in kb.inline_keyboard for b in row)
