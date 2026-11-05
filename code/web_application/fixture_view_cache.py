import logging
import os
from typing import TYPE_CHECKING

import redis
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from models import Fixture


logger = logging.getLogger(__name__)

PREFIX = os.getenv("PREFIX", "s2383")


class FixtureViewCache:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    def increment_fixture_views(self, fixture: "Fixture", db: Session) -> int:
        count = self.redis_client.incr(f"{PREFIX}:views:fixture:{fixture.id}")

        if count % 10 == 0:
            fixture.view_count = count
            db.commit()
            logger.info(
                "Synced views to database: fixture_id=%s view_count=%s",
                fixture.id,
                count,
            )

        return count


fixture_view_cache = FixtureViewCache(
    redis.Redis(
        host=os.getenv("REDIS_HOST", "127.0.0.1"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )
)
