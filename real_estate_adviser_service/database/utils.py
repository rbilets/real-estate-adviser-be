import pandas as pd
from datetime import datetime
from sqlalchemy import Engine, text


def read_historical_property_data(engine: Engine, city: str, state: str):
    query = f"""
    SELECT * FROM HistoricalPropertyData
    WHERE city = '{city.capitalize()}' and state = '{state.upper()}'
    """

    df = pd.read_sql(query, engine)
    return df


def write_historical_property_data(engine: Engine, df):
    df.to_sql(
        "HistoricalPropertyData",
        con=engine,
        index=False,
        if_exists="append",
        chunksize=5000,
    )


def remove_location_from_db(
    engine: Engine, city: str, state: str, last_sold_date: datetime = None
):
    query_text = """
    DELETE FROM HistoricalPropertyData
    WHERE city = :city AND state = :state
    """

    params = {"city": city.capitalize(), "state": state.upper()}

    if last_sold_date:
        query_text += " AND last_sold_date >= :last_sold_date"
        params["last_sold_date"] = last_sold_date

    delete_query = text(query_text)

    with engine.connect() as connection:
        with connection.begin() as transaction:
            try:
                result = connection.execute(delete_query, params)
                transaction.commit()
                print(f"Deleted {result.rowcount} rows.")
            except Exception as e:
                print("An error occurred:", e)
                transaction.rollback()
