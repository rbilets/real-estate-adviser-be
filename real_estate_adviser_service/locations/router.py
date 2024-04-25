from fastapi import APIRouter, Query

from typing import List
from locations.schemas import Location
from locations import service
from database.database import DbEngine


router = APIRouter()


@router.get("/locations", operation_id="get_locations")
def get_locations(db_engine: DbEngine) -> List[Location]:
    return service.get_added_locations(engine=db_engine)
