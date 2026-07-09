from config.topics import TOPICS, TOPIC_BY_KEY, DEMO_POSTS, SOURCES


def test_topics_count():
    assert len(TOPICS) == 5


def test_topic_keys_unique():
    keys = [t["key"] for t in TOPICS]
    assert len(keys) == len(set(keys))


def test_topic_by_key_resolves():
    for t in TOPICS:
        assert TOPIC_BY_KEY[t["key"]] is t


def test_each_topic_has_keywords():
    for t in TOPICS:
        assert t["keywords"], f"topic {t['key']} has no keywords"


def test_demo_posts_have_valid_topic():
    for post in DEMO_POSTS:
        assert post["topic_key"] in TOPIC_BY_KEY
        assert post["source"] in SOURCES
        assert post["url"].startswith("http")
        assert post["title"]
