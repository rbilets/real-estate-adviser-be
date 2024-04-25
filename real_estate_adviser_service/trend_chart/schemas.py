from pydantic import BaseModel
from typing import List, Optional


class DataPoint(BaseModel):
    year: int
    avg_price: Optional[int]
    properties_sold: int
    percentage_change: Optional[float]


class TrendChartResponse(BaseModel):
    styles: List[str]
    avg_year_percent_change: Optional[float]
    chart_data: List[DataPoint]
