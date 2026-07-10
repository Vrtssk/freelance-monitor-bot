import pytest

from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards import (
    main_menu_kb,
    topics_kb,
    back_kb,
    demo_kb,
    settings_kb,
)
from config.topics import TOPICS


def test_main_menu_has_6_buttons():
    kb = main_menu_kb()
    assert kb.inline_keyboard is not None
    total = sum(len(row) for row in kb.inline_keyboard)
    assert total == 6
    labels = " ".join(b.text for row in kb.inline_keyboard for b in row)
    assert "Топ-5" in labels


def test_topics_kb_includes_all_topics_plus_done():
    kb = topics_kb(set())
    labels = " ".join(b.text for row in kb.inline_keyboard for b in row)
    for t in TOPICS:
        assert t["name"] in labels
    assert "Готово" in labels


def test_topics_kb_marks_selected():
    kb = topics_kb({TOPICS[0]["key"]})
    first_row_text = kb.inline_keyboard[0][0].text
    assert "✅" in first_row_text
    second_row_text = kb.inline_keyboard[1][0].text
    assert "☐" in second_row_text


def test_back_kb_has_back_button():
    kb = back_kb()
    assert kb.inline_keyboard[0][0].text.startswith("◀️")


def test_demo_kb_has_next_and_menu():
    kb = demo_kb()
    labels = " ".join(b.text for row in kb.inline_keyboard for b in row)
    assert "Следующее" in labels
    assert "В меню" in labels


def test_settings_kb_toggle_label_depends_on_state():
    paused_kb = settings_kb(paused=True)
    active_kb = settings_kb(paused=False)
    paused_labels = " ".join(b.text for row in paused_kb.inline_keyboard for b in row)
    active_labels = " ".join(b.text for row in active_kb.inline_keyboard for b in row)
    assert "Возобновить" in paused_labels
    assert "Пауза" in active_labels
