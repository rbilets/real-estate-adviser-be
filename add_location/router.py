from fastapi import APIRouter, HTTPException
from add_location.schemas import Location
from add_location import service
from locations.service import get_location_names
from common import format_location

router = APIRouter()


@router.post("/add_location", operation_id="add_location")
def add_location(location_data: Location):
    location, city, state = format_location(location_data.location)

    try:
        service.initialize_location(location=location, city=city, state=state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "message": f"Processed location: {location}"}
