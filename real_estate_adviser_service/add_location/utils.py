import geopy.distance
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
import pickle
import uuid
from sqlalchemy import Engine
import requests

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import DBSCAN

from sklearn.metrics import explained_variance_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import r2_score

from homeharvest import scrape_property
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, BlobBlock

from config import config
from database.utils import (
    read_historical_property_data,
    write_historical_property_data,
    remove_location_from_db,
    add_model_score,
)


def scrape_historical_sales(engine: Engine, location: str, city: str, state: str):
    sql_df = read_historical_property_data(engine, city, state)

    if len(sql_df) == 0:
        latest_ts = None
    else:
        sql_df["last_sold_date"] = pd.to_datetime(
            sql_df["last_sold_date"], errors="coerce"
        )
        latest_ts = sql_df["last_sold_date"].max()

    date_format = "%Y-%m-%d"
    increment = timedelta(days=config.hist_batch_incr_days)

    if latest_ts is None:
        start_date = datetime(year=config.hist_start_year, month=1, day=1)
    else:
        remove_location_from_db(
            engine=engine, city=city, state=state, last_sold_date=latest_ts
        )
        start_date = latest_ts
    end_date = start_date + increment

    dataframes = []

    while start_date < datetime.utcnow():
        start_date_str = start_date.strftime(date_format)
        end_date_str = end_date.strftime(date_format)

        try:
            properties = scrape_property(
                location=location,
                listing_type="sold",
                date_from=start_date_str,
                date_to=end_date_str,
            )
            print(f"Start:{start_date_str} End:{end_date_str} Count:{len(properties)}")
            dataframes.append(properties)

        except ValueError as e:
            print(f"Start:{start_date_str} End:{end_date_str} Error:{str(e)}")

        start_date = end_date + timedelta(days=1)
        end_date += increment

    scraped_df = pd.concat(dataframes, ignore_index=True)

    scraped_df["style"] = scraped_df["style"].apply(lambda x: x.value if x else None)
    scraped_df.replace([np.inf, -np.inf, np.nan], None, inplace=True)
    scraped_df.drop(
        ["mls", "mls_id", "primary_photo", "alt_photos"], axis=1, inplace=True
    )

    print(scraped_df.info())
    write_historical_property_data(engine, scraped_df)

    combined_df = (
        pd.concat([scraped_df, sql_df], ignore_index=True)
        if len(sql_df) > 0
        else scraped_df
    )
    return combined_df


class PropertyDatasetProcessor:
    def __init__(self, df, city, is_training=True, planned_mortgage_rate=None):
        self.dataset = df
        self.city = city
        self.is_training = is_training
        self.planned_mortgage_rate = planned_mortgage_rate

        geolocator = Nominatim(user_agent="RealEstateAdvisor")
        location = geolocator.geocode(f"Downtown {city}")
        self.downtown_lat, self.downtown_lon = location.latitude, location.longitude

    @staticmethod
    def calc_baths_num(full_baths, half_baths):
        if pd.isna(full_baths) and pd.isna(half_baths):
            return 0.0
        elif pd.isna(full_baths):
            return half_baths * 0.5
        elif pd.isna(half_baths):
            return full_baths
        else:
            return full_baths + 0.5 * half_baths

    @staticmethod
    def calc_lat_lon_dist(lat1, lon1, lat2, lon2):
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return None
        return round(geopy.distance.geodesic((lat1, lon1), (lat2, lon2)).km, 1)

    @staticmethod
    def fetch_mortgage_rates(series_id="MORTGAGE30US"):
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "api_key": "d8dcefb8a2e7e77823eebd400f84ec42",
            "file_type": "json",
            "series_id": series_id,
        }
        response = requests.get(url, params=params)
        data = response.json()
        df = pd.DataFrame(data["observations"])
        df["date"] = pd.to_datetime(df["date"])
        return df[["date", "value"]]

    @staticmethod
    def filter_iqr(df, column):
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        return df[(df[column] >= Q1 - 1.5 * IQR) & (df[column] <= Q3 + 1.5 * IQR)]

    def clean_dataset(self):
        final_df: pd.DataFrame = self.dataset[(self.dataset.city == self.city)].copy()

        # Handling NULL values
        final_df["baths"] = final_df.apply(
            lambda row: self.calc_baths_num(row["full_baths"], row["half_baths"]),
            axis=1,
        )
        final_df["lot_sqft"] = final_df.apply(
            lambda row: 0.0 if pd.isna(row["lot_sqft"]) else row["lot_sqft"], axis=1
        )
        final_df["parking_garage"] = final_df.apply(
            lambda row: (
                0.0 if pd.isna(row["parking_garage"]) else row["parking_garage"]
            ),
            axis=1,
        )

        final_df.dropna(
            subset=[
                "zip_code",
                "beds",
                "sqft",
                "year_built",
                "sold_price",
                "lot_sqft",
                "parking_garage",
                "last_sold_date",
                "baths",
                "latitude",
                "longitude",
            ],
            inplace=True,
        )

        # FEATURE ENGINEERING

        # Adding mortgate rate
        final_df["last_sold_date"] = pd.to_datetime(final_df["last_sold_date"])
        final_df["sold_year"] = final_df["last_sold_date"].dt.year

        mortgage_rates = self.fetch_mortgage_rates()

        if self.is_training:
            mortgage_rates = mortgage_rates.sort_values(by="date")
            final_df = final_df.sort_values(by="last_sold_date")

            final_df = pd.merge_asof(
                final_df,
                mortgage_rates,
                left_on="last_sold_date",
                right_on="date",
                direction="backward",
            )
            final_df.rename(columns={"value": "mortgage_rate"}, inplace=True)
            final_df.drop(["date"], axis=1, inplace=True)
        else:
            if self.planned_mortgage_rate:
                final_df["mortgage_rate"] = self.planned_mortgage_rate
            else:
                latest_mortgage_date = mortgage_rates[
                    mortgage_rates["date"] == mortgage_rates["date"].max()
                ]
                latest_mortgage_rate = latest_mortgage_date["value"].iloc[0]
                final_df["mortgage_rate"] = latest_mortgage_rate

        # Adding age
        final_df["age"] = final_df.apply(
            lambda row: row["sold_year"] - row["year_built"], axis=1
        )
        final_df = final_df[final_df.age >= 0]

        # Adding distance to downtown
        final_df["distance_to_downtown"] = final_df.apply(
            lambda row: self.calc_lat_lon_dist(
                row["latitude"], row["longitude"], self.downtown_lat, self.downtown_lon
            ),
            axis=1,
        )

        # Filtering out outliers
        for col in ("sqft", "year_built", "distance_to_downtown"):
            final_df = self.filter_iqr(final_df, col)

        if self.is_training:
            dbscan = DBSCAN(eps=0.5, min_samples=10)
            final_df["cluster_label"] = dbscan.fit_predict(final_df[["sold_price"]])
            final_df = final_df[final_df["cluster_label"] != -1]
            final_df.drop(columns=["cluster_label"], inplace=True)

        return final_df


def train_model(dataset: pd.DataFrame):
    cols_to_drop = [
        "sold_price",
        "property_url",
        "status",
        "style",
        "street",
        "unit",
        "city",
        "state",
        "full_baths",
        "half_baths",
        "days_on_mls",
        "list_price",
        "list_date",
        "last_sold_date",
        "price_per_sqft",
        "latitude",
        "longitude",
        "stories",
        "hoa_fee",
    ]

    X = dataset.drop(cols_to_drop, axis=1)
    y = dataset["sold_price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_model.fit(X_train, y_train)

    # Predictions on the test set
    y_pred = rf_model.predict(X_test)

    # Calculate metrics
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    expl_rf = explained_variance_score(y_pred, y_test)

    print(f"R-squared: {r2:.2f}")
    print(f"Mean Absolute Error: {mae:.2f}")
    print(f"Mean Squared Error: {mse:.2f}")
    print(f"Root Mean Squared Error: {rmse:.2f}")
    print(f"Explained Variance Score: {expl_rf:.2f}")

    return rf_model, round(r2 * 100, 2)


def get_chunk_blocks(data, blob_client, chunk_size=4 * 1024 * 1024):
    block_list = []

    index = 0
    while index < len(data):
        chunk_data = data[index : index + chunk_size]

        if not chunk_data:
            break
        blk_id = str(uuid.uuid4())
        blob_client.stage_block(block_id=blk_id, data=chunk_data)
        block_list.append(BlobBlock(block_id=blk_id))

        index += chunk_size

    return block_list


def write_model_to_storage(
    engine: Engine, model, city: str, state: str, model_score: float
):
    serialized_model = pickle.dumps(model)

    blob_service_client = BlobServiceClient.from_connection_string(
        config.az_storage_conn_str
    )
    blob_name = f"{city.lower()}_{state.lower()}.pkl"
    blob_client = blob_service_client.get_blob_client(
        container=config.az_storage_container_name, blob=blob_name
    )

    block_list = get_chunk_blocks(
        serialized_model, blob_client, chunk_size=4 * 1024 * 1024
    )
    blob_client.commit_block_list(block_list)
    add_model_score(engine=engine, model_name=blob_name, score=model_score)
    print(f"{blob_name} uploaded successfully.")
