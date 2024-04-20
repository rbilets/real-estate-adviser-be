import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from active_listings.router import router as active_listings_router
from add_location.router import router as add_location_router
from locations.router import router as added_locations_router


app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(active_listings_router, prefix="", tags=["Endpoints"])
app.include_router(add_location_router, prefix="", tags=["Endpoints"])
app.include_router(added_locations_router, prefix="", tags=["Endpoints"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
