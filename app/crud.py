from pymongo.collection import Collection
from bson import ObjectId
from typing import List, Optional
from datetime import datetime
import folium

from .database import (
    get_live_flights_collection, 
    get_completed_logs_collection
)
from .models import FlightCreate, FlightInDB, IngestData, LocationPoint

# Get database collections
live_flights_coll = get_live_flights_collection()
completed_logs_coll = get_completed_logs_collection()


async def create_flight(flight_data: FlightCreate) -> FlightInDB:
    """
    Creates a new 'SCHEDULED' flight in the live_flights collection.
    This is the admin API to register a flight before it takes off.
    """
    flight_doc = flight_data.dict()
    flight_doc["status"] = "SCHEDULED"
    flight_doc["last_update"] = datetime.now(datetime.utcnow().tzinfo)
    flight_doc["track"] = []
    
    insert_result = live_flights_coll.insert_one(flight_doc)
    new_flight = live_flights_coll.find_one({"_id": insert_result.inserted_id})
    return FlightInDB(**new_flight)


async def ingest_location(data: IngestData) -> Optional[FlightInDB]:
    """
    Ingests a new location point for a flight.
    This is the "radio signal" API.
    It finds the flight and $push-es the new location to its 'track' array.
    """
    # Create the sub-document for the track array
    location_point = LocationPoint(
        timestamp=data.timestamp,
        latitude=data.latitude,
        longitude=data.longitude,
        altitude=data.altitude,
        speed=data.speed
    )

    # Update the flight document in one atomic operation
    updated_flight = live_flights_coll.find_one_and_update(
        {"flight_id": data.flight_id},
        {
            "$push": {"track": location_point.dict()},
            "$set": {
                "last_update": data.timestamp,
                "status": "EN-ROUTE" # Set to EN-ROUTE on first data ingest
            }
        },
        return_document=True # Return the *new* updated document
    )
    
    if updated_flight:
        return FlightInDB(**updated_flight)
    return None # Flight not found in live collection


async def get_flight_track(flight_id: str) -> Optional[FlightInDB]:
    """
    Gets the full tracking information for a flight.
    It checks the 'live_flights' collection first,
    then checks the 'completed_flights_log' if not found.
    """
    flight_doc = live_flights_coll.find_one({"flight_id": flight_id})
    if flight_doc:
        return FlightInDB(**flight_doc)
    
    # If not found in live, check the logs
    flight_doc_log = completed_logs_coll.find_one({"flight_id": flight_id})
    if flight_doc_log:
        return FlightInDB(**flight_doc_log)
        
    return None # Not found in either collection


async def complete_flight(flight_id: str) -> Optional[FlightInDB]:
    """
    Moves a flight from the 'live_flights' collection to the
    'completed_flights_log' collection.
    This fulfills the data lifecycle requirement.
    """
    # 1. Find the flight in the live collection
    flight_doc = live_flights_coll.find_one({"flight_id": flight_id})
    
    if not flight_doc:
        return None # Flight not found or already completed

    # 2. Update status to 'LANDED'
    flight_doc["status"] = "LANDED"
    flight_doc["last_update"] = datetime.now(datetime.utcnow().tzinfo)

    # 3. Insert it into the completed logs collection
    completed_logs_coll.insert_one(flight_doc)
    
    # 4. Delete it from the live flights collection
    live_flights_coll.delete_one({"_id": flight_doc["_id"]})
    
    return FlightInDB(**flight_doc)


async def generate_map_html(flight: FlightInDB) -> str:
    """
    BONUS FUNCTION:
    Generates an interactive HTML map using Folium.
    """
    if not flight.track:
        return "<h1>No tracking data available for this flight.</h1>"

    # Get the list of (lat, lon) coordinates
    coordinates = [(point.latitude, point.longitude) for point in flight.track]
    
    # Calculate the center of the map
    avg_lat = sum(p[0] for p in coordinates) / len(coordinates)
    avg_lon = sum(p[1] for p in coordinates) / len(coordinates)
    
    # Create a Folium map
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=4)
    
    # Add the flight path as a line
    folium.PolyLine(
        locations=coordinates,
        color="blue",
        weight=3,
        opacity=0.8
    ).add_to(m)
    
    # Add a marker for the start point
    start_point = flight.track[0]
    folium.Marker(
        location=[start_point.latitude, start_point.longitude],
        popup=f"<b>Start: {flight.origin}</b><br>Time: {start_point.timestamp}",
        icon=folium.Icon(color="green")
    ).add_to(m)
    
    # Add a marker for the last known point
    end_point = flight.track[-1]
    popup_text = f"<b>Last Location</b><br>Time: {end_point.timestamp}<br>Speed: {end_point.speed} kts"
    if flight.status == "LANDED":
        popup_text = f"<b>Landed: {flight.destination}</b><br>Time: {end_point.timestamp}"
        
    folium.Marker(
        location=[end_point.latitude, end_point.longitude],
        popup=popup_text,
        icon=folium.Icon(color="red")
    ).add_to(m)
    
    # Return the map as an HTML string
    return m._repr_html_()