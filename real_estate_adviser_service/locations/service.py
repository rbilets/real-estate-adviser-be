from azure.storage.blob import BlobServiceClient
from typing import Optional

from config import config
from locations.schemas import Location
from sqlalchemy import Engine
from database.utils import get_model_scores


def get_added_locations(engine: Optional[Engine] = None):
    """
    If engine is passed, returns also model_score and score_calculated.
    """
    blob_service_client = BlobServiceClient.from_connection_string(
        config.az_storage_conn_str
    )
    container_client = blob_service_client.get_container_client(
        config.az_storage_container_name
    )

    models_list = container_client.list_blobs()
    model_scores = get_model_scores(engine=engine) if engine else {}

    locations = [
        Location(
            file_name=model.name,
            location=f"{model.name.split('.')[0].split('_')[0].title()}, {model.name.split('.')[0].split('_')[1].upper()}",
            city=model.name.split(".")[0].split("_")[0].title(),
            state=model.name.split(".")[0].split("_")[1].upper(),
            last_modified=model.last_modified,
            size_mb=round(model.size / 1048576, 2),
            score=model_scores.get(model.name)
            and model_scores.get(model.name).get("score"),
            score_calculated=model_scores.get(model.name)
            and model_scores.get(model.name).get("timestamp"),
        )
        for model in models_list
    ]
    return locations


def get_location_names():
    locations = get_added_locations()
    return [location.location for location in locations]
