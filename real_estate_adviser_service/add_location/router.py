from fastapi import APIRouter, HTTPException
from add_location import service
from common import format_location
from database.database import DbEngine
from add_location.schemas import Location

router = APIRouter()


@router.post("/add_location", operation_id="add_location")
def add_location(db_engine: DbEngine, location: Location):
    location, city, state = format_location(location.location)

    try:
        service.initialize_location(
            engine=db_engine, location=location, city=city, state=state
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "message": f"Processed location: {location}"}
