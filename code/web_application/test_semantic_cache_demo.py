import unittest

from semantic_cache_demo import summarize


class SemanticCacheDemoTests(unittest.TestCase):
    def test_summary_separates_hit_and_miss_latency(self):
        summary = summarize(
            [
                {"is_cached": False, "latency_ms": 100.0},
                {"is_cached": True, "latency_ms": 10.0},
                {"is_cached": True, "latency_ms": 20.0},
            ]
        )

        self.assertEqual(summary["cache_hit_rate_percent"], 66.67)
        self.assertEqual(summary["average_cached_latency_ms"], 15.0)
        self.assertEqual(summary["average_non_cached_latency_ms"], 100.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
