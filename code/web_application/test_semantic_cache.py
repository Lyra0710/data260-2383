import unittest

import redis
from semantic_cache import SemanticResponseCache


class FakeDocument:
    answer = "Cached answer"
    data_version = "0"
    distance = "0.1"


class FakeSearchResult:
    docs = [FakeDocument()]


class FakeSearch:
    def __init__(self):
        self.index_created = False

    def info(self):
        if not self.index_created:
            raise redis.ResponseError("Unknown Index name")

    def create_index(self, schema, definition):
        self.index_created = True

    def search(self, query, query_params):
        return FakeSearchResult()


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.search = FakeSearch()
        self.entries = {}

    def setnx(self, key, value):
        self.values.setdefault(key, value)

    def get(self, key):
        return self.values.get(key)

    def ft(self, index_name):
        return self.search

    def hset(self, key, mapping):
        self.entries[key] = mapping


class SemanticResponseCacheTests(unittest.TestCase):
    def setUp(self):
        self.redis_client = FakeRedis()
        self.cache = SemanticResponseCache(self.redis_client)

    def test_current_data_version_defaults_to_zero(self):
        self.assertEqual(self.cache.current_data_version(), "0")

    def test_matching_version_above_threshold_is_a_hit(self):
        response = self.cache.find_similar(
            [0.1, 0.2],
            "0",
            "user-1",
            "session-1",
            0.85,
        )

        self.assertEqual(response["answer"], "Cached answer")
        self.assertAlmostEqual(response["similarity_score"], 0.9)

    def test_stale_or_low_similarity_match_is_a_miss(self):
        self.assertIsNone(
            self.cache.find_similar([0.1, 0.2], "1", "user-1", "session-1", 0.85)
        )
        self.assertIsNone(
            self.cache.find_similar([0.1, 0.2], "0", "user-1", "session-1", 0.95)
        )

    def test_store_writes_required_cache_fields(self):
        self.cache.store(
            "Question",
            [0.1, 0.2],
            "Answer",
            "0",
            "user-1",
            "session-1",
        )

        entry = next(iter(self.redis_client.entries.values()))
        self.assertEqual(entry["query"], "Question")
        self.assertEqual(entry["answer"], "Answer")
        self.assertEqual(entry["data_version"], "0")
        self.assertEqual(entry["user_id"], "user-1")
        self.assertEqual(entry["session_id"], "session-1")
        self.assertIsInstance(entry["embedding"], bytes)

    def test_escape_tag_escapes_redis_tag_characters(self):
        self.assertEqual(
            SemanticResponseCache.escape_tag("user-1{a}|$"),
            r"user\-1\{a\}\|\$",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
