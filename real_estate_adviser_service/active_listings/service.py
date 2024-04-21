from typing import Optional
import numpy as np
from cachetools import TTLCache
import re


from active_listings.utils import (
    scrape_active_sales,
    read_model_from_storage,
    predict_sale_prices,
    filter_properties,
)
from add_location.utils import PropertyDatasetProcessor


cache = TTLCache(maxsize=10, ttl=1800)


def _get_cache_key(location: str):
    return str(hash(f"{location.lower().replace(' ', '')}"))


def get_active_listings(
    location: str,
    city: str,
    state: str,
    min_price: int,
    max_price: int,
    sort_by_year: int,
    amount: int,
):
    cache_key = _get_cache_key(location)
    if cache_key in cache:
        return filter_properties(
            cache[cache_key],
            min_price=min_price,
            max_price=max_price,
            sold_year=sort_by_year,
            amount=amount,
        )

    raw_sales_df = scrape_active_sales(location)
    rf_model = read_model_from_storage(city, state)
    properties_df = PropertyDatasetProcessor(raw_sales_df, city).clean_dataset()
    predict_prices_df = predict_sale_prices(properties_df, rf_model)
    predict_prices_df.replace([np.inf, -np.inf, np.nan], None, inplace=True)
    result = predict_prices_df.to_dict(orient="records")

    cache[cache_key] = result
    return filter_properties(
        result,
        min_price=min_price,
        max_price=max_price,
        sold_year=sort_by_year,
        amount=amount,
    )
