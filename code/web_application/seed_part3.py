from random import Random

from sqlalchemy import delete, select

from db import SessionLocal
from models import Fixture, FixtureRelatedItem


SEED = 2383
FIXTURE_COUNT = 5_000
RELATED_ITEM_COUNT = 200
FIXTURE_PREFIX = "HW4 Fixture"


def remove_previous_seed_data(db):
    seeded_fixtures = db.scalars(
        select(Fixture).where(
            Fixture.fixture_name.like(f"{FIXTURE_PREFIX} %")
        )
    ).all()

    fixture_ids = [
        fixture.id
        for fixture in seeded_fixtures
    ]

    if not fixture_ids:
        return

    db.execute(
        delete(FixtureRelatedItem).where(
            FixtureRelatedItem.fixture_id.in_(fixture_ids)
        )
    )
    db.execute(
        delete(Fixture).where(
            Fixture.id.in_(fixture_ids)
        )
    )
    db.flush()


def seed_database():
    random_generator = Random(SEED)
    db = SessionLocal()

    try:
        remove_previous_seed_data(db)

        fixtures = []

        for number in range(1, FIXTURE_COUNT + 1):
            first_team = random_generator.randint(1, 100)
            second_team = random_generator.randint(1, 100)

            fixture = Fixture(
                fixture_name=f"{FIXTURE_PREFIX} {number:04d}",
                teams=f"Team {first_team} vs Team {second_team}",
            )
            fixtures.append(fixture)

        db.add_all(fixtures)
        db.flush()

        related_fixtures = random_generator.sample(
            fixtures,
            RELATED_ITEM_COUNT,
        )

        related_items = [
            FixtureRelatedItem(
                fixture_id=fixture.id,
                label="Match note",
                details=f"Generated related item for {fixture.fixture_name}.",
            )
            for fixture in related_fixtures
        ]

        db.add_all(related_items)
        db.commit()

        print(f"Seeded {FIXTURE_COUNT} fixtures.")
        print(f"Seeded {RELATED_ITEM_COUNT} related items.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()