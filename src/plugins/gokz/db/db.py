import os
import urllib.parse

from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine
from . import models

load_dotenv()


def get_url():
    user = os.getenv("MYSQL_USER", "root")
    password = urllib.parse.quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    server = os.getenv("MYSQL_SERVER", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    db_name = os.getenv("MYSQL_DB", "app")
    return f"mysql+pymysql://{user}:{password}@{server}:{port}/{db_name}"


engine = create_engine(get_url())


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def init_db():
    pass


if __name__ == '__main__':
    print(get_url())
    create_db_and_tables()
