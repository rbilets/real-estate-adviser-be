import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.az_storage_conn_str = os.getenv("AZ_STORAGE_CONN_STR")
        self.az_storage_container_name = os.getenv("AZ_STORAGE_CONTAINER_NAME")
        self.yrs_to_predict = int(os.getenv("YEARS_TO_PREDICT"))
        self.hist_start_year = int(os.getenv("HISTORICAL_START_YEAR"))
        self.hist_batch_incr_days = int(os.getenv("HISTORICAL_BATCH_INCREMENT_DAYS"))
        self.active_listing_days = int(os.getenv("LOAD_ACTIVE_LISTINGS_DAYS"))

        self.db_host = os.getenv("DB_HOST")
        self.db_name = os.getenv("DB_NAME")
        self.db_port = os.getenv("DB_PORT")
        self.db_username = os.getenv("DB_USERNAME")
        self.db_password = os.getenv("DB_PASSWORD")


config = Config()
