from fastapi import APIRouter, Query

from typing import List
from real_estate_adviser_service.locations.schemas import Location
from real_estate_adviser_service.locations import service


router = APIRouter()


@router.get("/locations", operation_id="get_locations")
def get_locations() -> List[Location]:
    return service.get_added_locations()
