import geopy.distance
import pandas as pd
from geopy.geocoders import Nominatim
import pickle
import time
import uuid

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import explained_variance_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import mean_squared_error
from homeharvest import scrape_property
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, BlobBlock

from real_estate_adviser_service.config import config


def scrape_historical_sales(location):
    date_format = "%Y-%m-%d"
    increment = timedelta(days=config.hist_batch_incr_days)
    start_date = datetime(year=config.hist_start_year, month=1, day=1)
    end_date = start_date + increment

    dataframes = []

    while start_date < datetime.utcnow():
        start_date_str = start_date.strftime(date_format)
        end_date_str = end_date.strftime(date_format)

        try:
            properties = scrape_property(
                location=location,
                listing_type="sold",  # or (for_sale, for_rent)
                date_from=start_date_str,
                date_to=end_date_str,
            )
            print(f"Start:{start_date_str} End:{end_date_str} Count:{len(properties)}")
            dataframes.append(properties)

        except ValueError as e:
            print(f"Start:{start_date_str} End:{end_date_str} Error:{str(e)}")

        start_date = end_date + timedelta(days=1)
        end_date += increment

    combined_df = pd.concat(dataframes, ignore_index=True)
    print(combined_df.info())
    return combined_df


class PropertyDatasetProcessor:
    def __init__(self, df, city):
        self.dataset = df
        self.city = city

        geolocator = Nominatim(user_agent="RealEstateAdvisor")
        location = geolocator.geocode(f"Downtown {city}")
        self.downtown_lat, self.downtown_lon = location.latitude, location.longitude

    @staticmethod
    def calc_lat_lon_dist(lat1, lon1, lat2, lon2):
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return None
        return round(geopy.distance.geodesic((lat1, lon1), (lat2, lon2)).km, 1)

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

    def clean_dataset(self):
        dataset = self.dataset[(self.dataset.city == self.city)]

        dataset["distance_to_downtown"] = dataset.apply(
            lambda row: self.calc_lat_lon_dist(
                row["latitude"], row["longitude"], self.downtown_lat, self.downtown_lon
            ),
            axis=1,
        )
        dataset["baths"] = dataset.apply(
            lambda row: self.calc_baths_num(row["full_baths"], row["half_baths"]),
            axis=1,
        )
        dataset["sqft"] = dataset.apply(
            lambda row: (
                0.0 if pd.isna(row["sqft"]) and row["style"] == "LAND" else row["sqft"]
            ),
            axis=1,
        )
        dataset["style"] = dataset.apply(
            lambda row: "OTHER" if pd.isna(row["style"]) else row["style"], axis=1
        )
        dataset["lot_sqft"] = dataset.apply(
            lambda row: 0.0 if pd.isna(row["lot_sqft"]) else row["lot_sqft"], axis=1
        )
        dataset["hoa_fee"] = dataset.apply(
            lambda row: 0.0 if pd.isna(row["hoa_fee"]) else row["hoa_fee"], axis=1
        )
        dataset["stories"] = dataset.apply(
            lambda row: 0.0 if pd.isna(row["stories"]) else row["stories"], axis=1
        )
        dataset["beds"] = dataset.apply(
            lambda row: 0.0 if pd.isna(row["beds"]) else row["beds"], axis=1
        )
        dataset["sold_year"] = pd.to_datetime(dataset["last_sold_date"]).apply(
            lambda x: x.year
        )

        dataset.dropna(
            subset=["year_built", "sqft", "distance_to_downtown", "parking_garage"],
            inplace=True,
        )
        dataset["age"] = dataset.apply(
            lambda row: row["sold_year"] - row["year_built"], axis=1
        )

        return dataset


def train_model(dataset):
    cols_to_drop = [
        "property_url",
        "status",
        "street",
        "unit",
        "city",
        "state",
        "days_on_mls",
        "list_price",
        "list_date",
        "latitude",
        "longitude",
        "primary_photo",
        "mls",
        "mls_id",
        "price_per_sqft",
        "alt_photos",
        "style",
        "full_baths",
        "half_baths",
        "last_sold_date",
        "sold_price",
    ]

    X = dataset.drop(cols_to_drop, axis=1)
    y = dataset["sold_price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_model.fit(X_train, y_train)
    model_score = rf_model.score(X_test, y_test)
    print(f"Model trained with the score: {model_score}")

    return rf_model


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


def write_model_to_storage(model, city: str, state: str):
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

    print(f"{blob_name} uploaded successfully.")
