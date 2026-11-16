import unittest

from fixture_view_cache import FixtureViewCache


class FakeRedis:
    def __init__(self):
        self.values = {}

    def incr(self, key):
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]


class FakeFixture:
    def __init__(self, fixture_id):
        self.id = fixture_id
        self.view_count = 0


class FakeSession:
    def __init__(self, fixture):
        self.fixture = fixture
        self.commit_count = 0

    def commit(self):
        self.commit_count += 1


class FixtureViewCacheTests(unittest.TestCase):
    def test_counter_syncs_every_ten_views(self):
        fixture = FakeFixture(7)
        session = FakeSession(fixture)
        cache = FixtureViewCache(FakeRedis())

        with self.assertLogs("fixture_view_cache", level="INFO") as logs:
            counts = [
                cache.increment_fixture_views(fixture, session) for _ in range(25)
            ]

        self.assertEqual(counts, list(range(1, 26)))
        self.assertEqual(fixture.view_count, 20)
        self.assertEqual(session.commit_count, 2)
        self.assertEqual(len(logs.output), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
