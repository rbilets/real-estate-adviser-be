from fastapi import APIRouter, Query, HTTPException
from datetime import datetime

from typing import List
from active_listings import service
from active_listings.schemas import Listing
from locations.service import get_location_names
from common import format_location


router = APIRouter()


@router.get("/active-listings", operation_id="active_listings")
def get_active_listings(
    location: str = Query(..., description="Location"),
    amount: int = Query(None, description="Listings amount"),
) -> List[Listing]:
    location, city, state = format_location(location)

    if location not in get_location_names():
        raise HTTPException(status_code=404, detail=f"Location {location} not found. Please add it.")

    try:
        return service.get_active_listings(
        location=location,
        city=city,
        state=state,
        amount=amount
    )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
