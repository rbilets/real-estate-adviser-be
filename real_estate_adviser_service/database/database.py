from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

from config import config


def get_engine():
    connection_url = URL.create(
        "mssql+pyodbc",
        username=config.db_username,
        password=config.db_password,
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        query={"driver": "ODBC Driver 17 for SQL Server"},
    )

    engine = create_engine(
        connection_url,
        echo=True,  # debug information
        fast_executemany=True,
    )
    return engine


DbEngine = Annotated[Engine, Depends(get_engine)]
