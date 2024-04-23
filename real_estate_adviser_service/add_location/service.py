from sqlalchemy.engine import Engine

from add_location.utils import (
    scrape_historical_sales,
    PropertyDatasetProcessor,
    train_model,
    write_model_to_storage,
)


def initialize_location(engine: Engine, location: str, city: str, state: str):
    df = scrape_historical_sales(
        engine=engine, location=location, city=city, state=state
    )
    dataset = PropertyDatasetProcessor(df, city).clean_dataset()
    model = train_model(dataset)
    write_model_to_storage(model, city, state)
