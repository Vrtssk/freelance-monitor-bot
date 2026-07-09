from bot.handlers.demo import format_post
from config.topics import DEMO_POSTS, TOPIC_BY_KEY, SOURCES


def test_format_post_contains_title_and_budget():
    post = DEMO_POSTS[0]
    text = format_post(post, index=0, total=len(DEMO_POSTS))
    assert post["title"] in text
    assert post["budget"] in text
    assert "Новое объявление" in text


def test_format_post_uses_topic_label():
    post = DEMO_POSTS[0]
    topic = TOPIC_BY_KEY[post["topic_key"]]
    text = format_post(post, index=0, total=len(DEMO_POSTS))
    assert f"{topic['emoji']} {topic['name']}" in text


def test_format_post_uses_source_info():
    post = DEMO_POSTS[0]
    src = SOURCES[post["source"]]
    text = format_post(post, index=0, total=len(DEMO_POSTS))
    assert src["name"] in text
    assert src["emoji"] in text
    assert post["url"] in text


def test_format_post_index_counter():
    post = DEMO_POSTS[2]
    text = format_post(post, index=2, total=5)
    assert "(3/5)" in text
