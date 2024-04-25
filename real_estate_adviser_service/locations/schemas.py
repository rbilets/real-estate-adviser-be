from pydantic import BaseModel
from datetime import datetime


class Location(BaseModel):
    file_name: str
    location: str
    city: str
    state: str
    last_modified: datetime
    size_mb: float
    score: float
    score_calculated: datetime
