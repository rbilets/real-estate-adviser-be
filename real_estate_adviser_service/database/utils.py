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


def add_model_score(engine: Engine, model_name: str, score: float):
    query = text(
        """
    MERGE INTO ModelScores AS target
    USING (VALUES (:model_name, :score, :timestamp)) AS source (model_name, score, [timestamp])
    ON target.model_name = source.model_name
    WHEN MATCHED THEN
        UPDATE SET target.score = source.score, target.[timestamp] = source.[timestamp]
    WHEN NOT MATCHED THEN
        INSERT (model_name, score, [timestamp])
        VALUES (source.model_name, source.score, source.[timestamp]);
    """
    )
    params = {
        "model_name": model_name,
        "score": score,
        "timestamp": datetime.utcnow(),
    }

    with engine.connect() as connection:
        with connection.begin() as transaction:
            try:
                connection.execute(query, params)
                transaction.commit()
                print(f"Added {score} score for {model_name}")
            except Exception as e:
                print("An error occurred:", e)
                transaction.rollback()


def get_model_scores(engine: Engine):
    query = text("SELECT * FROM ModelScores")
    with engine.connect() as connection:
        query_result = connection.execute(query).fetchall()

    model_scores = {}
    if query_result:
        for model_name, score, timestamp in query_result:
            model_scores[model_name] = {"score": score, "timestamp": timestamp}
    return model_scores
