from bot.handlers.refresh import _build_result


def test_build_result_skipped():
    text = _build_result({"skipped": True})
    assert "уже идёт" in text


def test_build_result_no_new():
    summary = {
        "sources": {
            "fl_ru": {"found": 30, "new": 0},
            "kwork": {"found": 12, "new": 0},
        },
        "notified": 0,
    }
    text = _build_result(summary)
    assert "нет" in text
    assert "42" in text  # total found 30+12


def test_build_result_with_new():
    summary = {
        "sources": {
            "fl_ru": {"found": 30, "new": 3},
            "kwork": {"found": 12, "new": 1},
        },
        "notified": 2,
    }
    text = _build_result(summary)
    assert "Отправлено" in text
    assert "4" in text  # total new 3+1
    assert "42" in text  # total found
