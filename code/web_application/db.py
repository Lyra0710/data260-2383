import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker


APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env")

socket_path = os.getenv("MYSQL_SOCKET")

connection_values = {
    "drivername": "mysql+pymysql",
    "username": os.environ["MYSQL_USER"],
    "password": os.environ["MYSQL_PASSWORD"],
    "database": os.environ["MYSQL_DATABASE"],
}

if not socket_path:
    connection_values["host"] = os.environ["MYSQL_HOST"]
    connection_values["port"] = int(os.environ["MYSQL_PORT"])

database_url = URL.create(**connection_values)

engine_options = {
    "pool_pre_ping": True,
}

if socket_path:
    engine_options["connect_args"] = {
        "unix_socket": socket_path,
    }

engine = create_engine(
    database_url,
    **engine_options,
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