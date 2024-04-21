from azure.storage.blob import BlobServiceClient

from config import config
from locations.schemas import Location


def get_added_locations():
    blob_service_client = BlobServiceClient.from_connection_string(
        config.az_storage_conn_str
    )
    container_client = blob_service_client.get_container_client(
        config.az_storage_container_name
    )

    models_list = container_client.list_blobs()

    locations = [
        Location(
            file_name=model.name,
            location=f"{model.name.rstrip('.pkl').split('_')[0].capitalize()}, {model.name.rstrip('.pkl').split('_')[1].upper()}",
            city=model.name.rstrip('.pkl').split("_")[0].capitalize(),
            state=model.name.rstrip('.pkl').split("_")[1].upper(),
            last_modified=model.last_modified,
            size_mb=round(model.size / 1048576, 2),
        )
        for model in models_list
    ]
    return locations


def get_location_names():
    locations = get_added_locations()
    return [location.location for location in locations]