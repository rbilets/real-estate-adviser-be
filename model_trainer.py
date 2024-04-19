import os
import geopy.distance
import numpy as np
import pandas as pd
from geopy.geocoders import Nominatim
import pickle
import time

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import explained_variance_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import mean_squared_error
from homeharvest import scrape_property
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


def scrape_historical_sales(location):
    date_format = "%Y-%m-%d"
    increment = timedelta(days=90)
    start_date = datetime(year=2015, month=1, day=1)
    end_date = start_date + increment

    dataframes = []

    while start_date < datetime.utcnow():
        start_date_str = start_date.strftime(date_format)
        end_date_str = end_date.strftime(date_format)

        # filename = f"data/{start_date_str}_{end_date_str}.csv"

        try:
            properties = scrape_property(
                location=location,
                listing_type="sold",  # or (for_sale, for_rent)
                date_from=start_date_str,
                date_to=end_date_str
            )
            print(f"Start:{start_date_str} End:{end_date_str} Count:{len(properties)}")
            dataframes.append(properties)

            # properties.to_csv(filename, index=False)
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

        dataset['distance_to_downtown'] = dataset.apply(lambda row: self.calc_lat_lon_dist(row['latitude'], row['longitude'], self.downtown_lat, self.downtown_lon), axis=1)
        dataset['baths'] = dataset.apply(lambda row: self.calc_baths_num(row["full_baths"], row["half_baths"]), axis=1)
        dataset['sqft'] = dataset.apply(lambda row: 0.0 if pd.isna(row["sqft"]) and row["style"] == "LAND" else row["sqft"], axis=1)
        dataset['style'] = dataset.apply(lambda row: "OTHER" if pd.isna(row["style"]) else row["style"], axis=1)
        dataset['lot_sqft'] = dataset.apply(lambda row: 0.0 if pd.isna(row["lot_sqft"]) else row["lot_sqft"], axis=1)
        dataset['hoa_fee'] = dataset.apply(lambda row: 0.0 if pd.isna(row["hoa_fee"]) else row["hoa_fee"], axis=1)
        dataset['stories'] = dataset.apply(lambda row: 0.0 if pd.isna(row["stories"]) else row["stories"], axis=1)
        dataset['beds'] = dataset.apply(lambda row: 0.0 if pd.isna(row["beds"]) else row["beds"], axis=1)
        dataset['sold_year'] = pd.to_datetime(dataset['last_sold_date']).apply(lambda x: x.year)

        dataset.dropna(subset=["year_built", "sqft", "distance_to_downtown", "parking_garage"], inplace=True)
        dataset['age'] = dataset.apply(lambda row: row["sold_year"] - row["year_built"], axis=1)

        return dataset


def train_model(dataset):
    cols_to_drop = ["property_url", "status", "street", "unit", "city", "state", "days_on_mls", "list_price", "list_date", "latitude", "longitude", "primary_photo", "mls", "mls_id", "price_per_sqft", "alt_photos", "style", "full_baths", "half_baths", "last_sold_date", "sold_price"]

    X = dataset.drop(cols_to_drop, axis=1)
    y = dataset['sold_price']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    rf_model = RandomForestRegressor(n_estimators=50,random_state=42)
    rf_model.fit(X_train, y_train)
    model_score = rf_model.score(X_test,y_test)
    print(f"Model trained with the score: {model_score}")
    
    return rf_model


def write_model_to_storage(model, city: str, state: str):
    serialized_model = pickle.dumps(model)

    connect_str = "DefaultEndpointsProtocol=https;AccountName=estateadviserstorage;AccountKey=Y52EdpNysG+MJetBBg7T+JeLfC/H8ZkB0HyGdRG+NItsVcY5KsKINikApihU4OqgERa2frz1gCVw+AStUiwuzg==;EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_name = "models"

    try:
        container_client = blob_service_client.create_container(container_name)
    except Exception as e:
        print("Container already exists or error in creation:", e)

    blob_name = f"{city.lower()}_{state.lower()}_model.pkl"
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    blob_client.upload_blob(serialized_model, overwrite=True)
    print(f"{blob_name} uploaded successfully.")


location = "Seattle, WA"
city, state = location.split(", ")

def main():
    df = scrape_historical_sales(location)
    dataset = PropertyDatasetProcessor(df, city).clean_dataset()
    model = train_model(dataset)
    write_model_to_storage(model, city, state)


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()


    duration_seconds = end_time - start_time
    duration_minutes = duration_seconds / 60

    print(f"The function took {duration_minutes:.2f} minutes to complete.")