from fastapi import APIRouter, HTTPException
from real_estate_adviser_service.add_location import service
from real_estate_adviser_service.common import format_location

router = APIRouter()


@router.post("/add_location", operation_id="add_location")
def add_location(location: str):
    location, city, state = format_location(location)

    try:
        service.initialize_location(location=location, city=city, state=state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "message": f"Processed location: {location}"}
