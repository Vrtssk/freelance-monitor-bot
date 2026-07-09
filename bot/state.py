from collections import defaultdict

selected_topics: dict[int, set[str]] = defaultdict(set)

monitoring_active: dict[int, bool] = {}

demo_index: dict[int, int] = {}
