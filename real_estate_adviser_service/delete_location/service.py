from azure.storage.blob import BlobServiceClient
from sqlalchemy import Engine

from database.utils import remove_location_from_db
from config import config


def delete_location(engine: Engine, city: str, state: str):
    remove_location_from_db(engine=engine, city=city, state=state, last_sold_date=None)

    blob_service_client = BlobServiceClient.from_connection_string(
        config.az_storage_conn_str
    )
    blob_name = f"{city.lower()}_{state.lower()}.pkl"
    blob_client = blob_service_client.get_blob_client(
        container=config.az_storage_container_name, blob=blob_name
    )

    blob_client.delete_blob()
