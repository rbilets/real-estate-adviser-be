from pydantic import BaseModel


class Location(BaseModel):
    location: str
