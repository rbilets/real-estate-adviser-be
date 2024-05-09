from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Location(BaseModel):
    file_name: str
    location: str
    city: str
    state: str
    last_modified: datetime
    size_mb: float
    score: Optional[float]
    score_calculated: Optional[datetime]
