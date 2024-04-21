import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from real_estate_adviser_service.active_listings.router import router as active_listings_router
from real_estate_adviser_service.add_location.router import router as add_location_router
from real_estate_adviser_service.delete_location.router import router as delete_location_router
from real_estate_adviser_service.locations.router import router as locations_router


app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(active_listings_router, prefix="", tags=["Listings"])
app.include_router(add_location_router, prefix="", tags=["Locations"])
app.include_router(delete_location_router, prefix="", tags=["Locations"])
app.include_router(locations_router, prefix="", tags=["Locations"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
