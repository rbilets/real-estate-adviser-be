from fastapi import HTTPException
import re
from locations.service import get_location_names


def format_location(location: str):
    error_msg = "Incorrect format of location. Correct format: Seattle, WA"
    try:
        location_formatted = re.split(r'\s*,\s*', location.lower())
        city, state = (
            location_formatted[0].capitalize(),
            location_formatted[1].upper(),
        )
        location = f"{city}, {state}"
    except:
        raise HTTPException(
            status_code=400, detail=error_msg
        )

    if not city or not state or not location or len(state) != 2:
        raise HTTPException(
            status_code=400, detail=error_msg
        )

    return location, city, state


def validate_is_location_added(location: str):
    available_locations = get_location_names()
    if location not in available_locations:
        avail_locs_str = ', '.join(available_locations) if available_locations else "None"
        raise HTTPException(status_code=404, detail=f"Location {location} was not found. Available locations: {avail_locs_str}")
