from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import HTMLResponse
from typing import List, Optional
from datetime import datetime

from . import crud
from . import models

app = FastAPI(
    title="FlightAware Mimic API",
    description="An API to ingest flight data and track flights.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    print("FastAPI application started...")
    # The DB connection is already established in database.py
    
@app.get("/")
def read_root():
    return {"message": "Welcome to the FlightAware Mimic API!"}


@app.post("/flights", 
          response_model=models.FlightInDB, 
          status_code=201,
          summary="Create a new scheduled flight")
async def create_new_flight(flight_data: models.FlightCreate):
    """
    Register a new flight in the system *before* it takes off.
    Sets the flight status to 'SCHEDULED'.
    """
    return await crud.create_flight(flight_data)


@app.post("/ingest", 
          response_model=models.FlightInDB,
          summary="Ingest a new location point (Radio Signal)")
async def ingest_flight_data(data: models.IngestData):
    """
    This is the main "radio signal" endpoint.
    Send a new location point for a flight.
    This will update the flight's status to 'EN-ROUTE' and
    add the point to its 'track' array.
    """
    updated_flight = await crud.ingest_location(data)
    if not updated_flight:
        raise HTTPException(status_code=404, detail="Flight ID not found in live tracking.")
    return updated_flight


@app.get("/track/{flight_id}", 
         response_model=models.FlightInDB,
         summary="Get full track for a flight (live or completed)")
async def get_flight_track_data(flight_id: str):
    """
    Fetches the entire track for a given flight.
    It checks for the flight in the live collection first,
    then checks the completed logs.
    """
    flight = await crud.get_flight_track(flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found.")
    return flight


@app.post("/flights/{flight_id}/complete", 
          response_model=models.FlightInDB,
          summary="Mark a flight as LANDED and archive it")
async def complete_and_archive_flight(flight_id: str):
    """
    This triggers the data lifecycle:
    1. Marks the flight as 'LANDED'.
    2. Moves the flight doc from 'live_flights' to 'completed_flights_log'.
    3. Deletes the flight from 'live_flights'.
    """
    archived_flight = await crud.complete_flight(flight_id)
    if not archived_flight:
        raise HTTPException(status_code=404, detail="Flight not found in live tracking.")
    return archived_flight


@app.get("/track/{flight_id}/map", 
         response_class=HTMLResponse,
         summary="BONUS: Get an interactive map of the flight path")
async def get_flight_map(flight_id: str):
    """
    This bonus endpoint generates and returns an interactive
    HTML map of the flight's path using Folium.
    """
    flight = await crud.get_flight_track(flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found.")
        
    html_map = await crud.generate_map_html(flight)
    return HTMLResponse(content=html_map)