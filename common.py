from fastapi import HTTPException
import re


def format_location(location: str):
    error_msg = "Incorrect format of location. Correct format: Seattle, WA"
    try:
        location_formatted = re.sub(r"\s+", "", location).lower()
        city, state = (
            location_formatted.split(",")[0].capitalize(),
            location_formatted.split(",")[1].upper(),
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
