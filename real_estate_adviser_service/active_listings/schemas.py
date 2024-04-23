from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class PredictPrice(BaseModel):
    sold_year: int
    sold_price: float
    percentage: float


class Listing(BaseModel):
    property_url: Optional[str]
    mls: Optional[str]
    mls_id: Optional[str]
    status: Optional[str]
    style: Optional[str]
    street: Optional[str]
    unit: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[int]
    beds: Optional[int]
    full_baths: Optional[int]
    half_baths: Optional[int]
    sqft: Optional[int]
    year_built: Optional[int]
    days_on_mls: Optional[int]
    list_price: Optional[int]
    list_date: Optional[datetime]
    last_sold_date: Optional[datetime]
    lot_sqft: Optional[int]
    price_per_sqft: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    stories: Optional[int]
    hoa_fee: Optional[int]
    parking_garage: Optional[int]
    primary_photo: Optional[str]
    alt_photos: Optional[List[str]]
    distance_to_downtown: Optional[float]
    baths: Optional[float]
    predicted_prices: Optional[List[PredictPrice]]
    percentage: float
