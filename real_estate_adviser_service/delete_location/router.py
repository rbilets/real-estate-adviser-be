from fastapi import APIRouter, HTTPException
from delete_location import service
from common import format_location, validate_is_location_added


router = APIRouter()


@router.delete("/delete_location", operation_id="delete_location")
def delete_location(location: str):
    location, city, state = format_location(location)

    validate_is_location_added(location)

    try:
        service.delete_location(location=location, city=city, state=state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"status": "success", "message": f"Deleted location: {location}"}
