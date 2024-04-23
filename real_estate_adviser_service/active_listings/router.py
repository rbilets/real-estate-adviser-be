from fastapi import APIRouter, Query, HTTPException

from active_listings import service
from common import format_location, validate_is_location_added


router = APIRouter()


@router.get("/active-listings", operation_id="active_listings")
def get_active_listings(
    location: str = Query(..., description="Location"),
    min_price: int = Query(None, description="Min Listing Price"),
    max_price: int = Query(None, description="Max Listing Price"),
    sort_by_year: int = Query(2024, description="Sort By Year"),
    amount: int = Query(None, description="Amount"),
):
    location, city, state = format_location(location)

    validate_is_location_added(location)

    try:
        return service.get_active_listings(
            location=location,
            city=city,
            state=state,
            min_price=min_price,
            max_price=max_price,
            sort_by_year=sort_by_year,
            amount=amount,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
