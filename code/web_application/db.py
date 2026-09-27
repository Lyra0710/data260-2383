import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker


APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env")

database_url = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["MYSQL_USER"],
    password=os.environ["MYSQL_PASSWORD"],
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", "8583")),
    database=os.getenv("MYSQL_DATABASE", "s2383_rel"),
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
)

db_session_basede26 = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = db_session_basede26()

    try:
        yield db
    finally:
        db.close()