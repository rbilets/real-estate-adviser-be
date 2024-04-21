from azure.storage.blob import BlobServiceClient
import config

from config import config

def delete_location(location:str, city: str, state: str):
    blob_service_client = BlobServiceClient.from_connection_string(config.az_storage_conn_str)
    blob_name = f"{city.lower()}_{state.lower()}.pkl"
    blob_client = blob_service_client.get_blob_client(container=config.az_storage_container_name, blob=blob_name)

    blob_client.delete_blob()
    
