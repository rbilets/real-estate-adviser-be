import time
import pickle
import pandas as pd
from azure.storage.blob import BlobServiceClient
from homeharvest import scrape_property
from datetime import date, timedelta

from model_trainer import PropertyDatasetProcessor


def read_model_from_storage(city, state):
    connect_str = "DefaultEndpointsProtocol=https;AccountName=estateadviserstorage;AccountKey=Y52EdpNysG+MJetBBg7T+JeLfC/H8ZkB0HyGdRG+NItsVcY5KsKINikApihU4OqgERa2frz1gCVw+AStUiwuzg==;EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_name = "models"
    blob_name = f"{city.lower()}_{state.lower()}_model.pkl"

    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=blob_name
    )
    blob_data = blob_client.download_blob().readall()

    model = pickle.loads(blob_data)
    return model


def scrape_active_sales(location):
    start_date = str(date.today() - timedelta(days=30))
    end_date = str(date.today())

    properties = scrape_property(
        location=location,
        listing_type="for_sale",
        date_from=start_date,
        date_to=end_date,
    )
    print(
        f"Properties listed on sale between {start_date} and {end_date}. Count:{len(properties)}"
    )

    return properties


def predict_sale_prices(properties_df, rf_model):
    years_to_predict = [date.today().year + i for i in range(0, 15, 5)]

    predicted_df = pd.concat(
        [properties_df.assign(sold_year=year) for year in years_to_predict],
        ignore_index=True,
    )
    predicted_df["age"] = predicted_df.apply(
        lambda row: row["sold_year"] - row["year_built"], axis=1
    )

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
    predicted_df["sold_price"] = rf_model.predict(
        predicted_df.drop(cols_to_drop, axis=1)
    )

    predicted_df["percentage"] = (
        predicted_df["sold_price"] / predicted_df["list_price"] - 1
    ) * 100

    predicted_df["predicted_prices"] = predicted_df.apply(
        lambda row: {
            "sold_year": row["sold_year"],
            "sold_price": row["sold_price"],
            "percentage": f"{row['percentage']:.2f}%",
        },
        axis=1,
    )

    exclude_columns = {
        "sold_year",
        "sold_price",
        "percentage",
        "predicted_prices",
        "age",
    }
    groupby_cols = [col for col in predicted_df.columns if col not in exclude_columns]

    final_df = (
        predicted_df.groupby(groupby_cols, dropna=False, sort=False)["predicted_prices"]
        .agg(list)
        .reset_index()
    )
    return final_df


def main():
    location = "Seattle, WA"
    city, state = location.split(", ")

    raw_sales_df = scrape_active_sales(location)
    rf_model = read_model_from_storage(city, state)
    properties_df = PropertyDatasetProcessor(raw_sales_df, city).clean_dataset()
    predict_prices_df = predict_sale_prices(properties_df, rf_model)
    result = predict_prices_df.to_json(orient="records")

    import json
    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f)
    return result


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()

    duration_seconds = end_time - start_time
    duration_minutes = duration_seconds / 60

    print(f"The function took {duration_minutes:.2f} minutes to complete.")
