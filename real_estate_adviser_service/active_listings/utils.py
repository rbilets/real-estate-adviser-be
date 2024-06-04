import pickle
import pandas as pd
from azure.storage.blob import BlobServiceClient
from homeharvest import scrape_property
from datetime import date, timedelta
from config import config


def read_model_from_storage(city: str, state: str):
    blob_service_client = BlobServiceClient.from_connection_string(
        config.az_storage_conn_str
    )
    blob_name = f"{city.lower()}_{state.lower()}.pkl"

    blob_client = blob_service_client.get_blob_client(
        container=config.az_storage_container_name, blob=blob_name
    )
    blob_data = blob_client.download_blob().readall()

    model = pickle.loads(blob_data)
    return model


def scrape_active_sales(location):
    start_date = str(date.today() - timedelta(days=config.active_listing_days))
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
    years_to_predict = [
        date.today().year + i for i in range(0, config.yrs_to_predict + 1, 2)
    ]

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
        "stories",
        "hoa_fee",
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
            "percentage": row["percentage"],
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
    final_df["alt_photos"] = final_df["alt_photos"].str.split(", ")
    return final_df


def filter_properties(
    properties, min_price=None, max_price=None, sold_year=2024, amount=None
):
    if min_price is not None:
        properties = [prop for prop in properties if prop["list_price"] >= min_price]
    if max_price is not None:
        properties = [prop for prop in properties if prop["list_price"] <= max_price]

    for prop in properties:
        year_data = next(
            (
                price
                for price in prop["predicted_prices"]
                if price["sold_year"] == sold_year
            ),
            None,
        )

        if year_data:
            prop["sort_percentage"] = year_data["percentage"]

    properties = sorted(
        properties, key=lambda x: x.get("sort_percentage", float("-inf")), reverse=True
    )
    if amount is not None:
        properties = properties[:amount]

    return properties
