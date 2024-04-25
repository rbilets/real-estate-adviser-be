from fastapi import APIRouter, Query, HTTPException

from trend_chart import service
from common import format_location, validate_is_location_added
from database.database import DbEngine


router = APIRouter()


@router.get("/trend_chart", operation_id="trend_chart")
def get_trend_chart(
    db_engine: DbEngine,
    location: str = Query(..., description="Location"),
    style: str = Query(None, description="Style"),
    min_beds: int = Query(None, description="Min Beds Amount"),
    max_beds: int = Query(None, description="Max Beds Amount"),
    min_baths: int = Query(None, description="Min Baths Amount"),
    max_baths: int = Query(None, description="Max Baths Amount"),
    min_sqft: int = Query(None, description="Min Sqft Amount"),
    max_sqft: int = Query(None, description="Max Sqft Amount"),
    min_stories: int = Query(None, description="Min Stories Amount"),
    max_stories: int = Query(None, description="Max Stories Amount"),
    year_built: int = Query(None, description="Year Built"),
):
    location, city, state = format_location(location)

    validate_is_location_added(location)

    try:
        return service.get_trend_chart_data(
            engine=db_engine,
            city=city,
            style=style,
            min_beds=min_beds,
            max_beds=max_beds,
            min_baths=min_baths,
            max_baths=max_baths,
            min_sqft=min_sqft,
            max_sqft=max_sqft,
            min_stories=min_stories,
            max_stories=max_stories,
            year_built=year_built,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
