from fastapi import APIRouter, Query

from typing import List
from locations.schemas import Location
from locations import service


router = APIRouter()


@router.get("/added_locations", operation_id="get_added_locations")
def get_added_locations() -> List[Location]:
    return service.get_added_locations()
