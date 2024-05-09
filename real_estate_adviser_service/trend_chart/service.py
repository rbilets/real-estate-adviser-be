from typing import Optional
from sqlalchemy import Engine, text
from jinja2 import Template

from common import get_query
from trend_chart.schemas import DataPoint, TrendChartResponse


def get_trend_chart_data(
    engine: Engine,
    city: str,
    style: Optional[str],
    min_beds: Optional[int],
    max_beds: Optional[int],
    min_baths: Optional[int],
    max_baths: Optional[int],
    min_sqft: Optional[int],
    max_sqft: Optional[int],
    min_stories: Optional[int],
    max_stories: Optional[int],
    year_built: Optional[int],
):
    styles_query = f"""
    SELECT DISTINCT [style] FROM [dbo].[HistoricalPropertyData] WHERE city = '{city}'
    """
    trend_chart_query = get_query(file_path="/trend_chart/trend_chart_query.jinja")
    parsed_chart_query = Template(trend_chart_query).render(
        city=city,
        style=style,
        min_beds=min_beds,
        max_beds=max_beds,
        min_baths=min_baths,
        max_baths=max_baths,
        min_sqft=min_sqft,
        max_sqft=max_sqft,
        min_stories=min_stories,
        max_stories=max_stories,
        year_built=year_built,
    )

    with engine.connect() as connection:
        styles_result = connection.execute(text(styles_query)).fetchall()
        chart_result = connection.execute(text(parsed_chart_query)).fetchall()

    styles = [style[0] for style in styles_result if style[0]]
    percentages, chart_data = [], []

    if style and style not in styles:
        raise ValueError(
            f"Incorrect style passed. Available styles: {', '.join(styles)}"
        )

    for year, avg_price, properties_sold, percentage_change in chart_result:
        if percentage_change:
            percentages.append(float(percentage_change))
        chart_data.append(
            DataPoint(
                year=year,
                avg_price=avg_price,
                properties_sold=properties_sold,
                percentage_change=percentage_change and float(percentage_change),
            )
        )

    return TrendChartResponse(
        styles=styles,
        avg_year_percent_change=(
            round(sum(percentages) / len(percentages), 2) if percentages else None
        ),
        chart_data=chart_data,
    )
