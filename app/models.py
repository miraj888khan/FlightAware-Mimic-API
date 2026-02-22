from pydantic import (
    BaseModel, 
    Field, 
    GetCoreSchemaHandler, 
    GetJsonSchemaHandler
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import List, Optional, Any
from datetime import datetime
from bson import ObjectId

# --- Custom PyObjectId model (Pydantic v2 compatible) ---
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        
        def validate_from_str(v: str) -> ObjectId:
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)

        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema(
                    [
                        core_schema.str_schema(),
                        core_schema.no_info_plain_validator_function(validate_from_str),
                    ]
                ),
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(lambda x: str(x)),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string"}

# --- Schema for the "Radio Signal" data point ---
class LocationPoint(BaseModel):
    """
    Represents a single location update (a 'ping') from a flight.
    """
    timestamp: datetime = Field(..., example="2026-01-10T09:30:00Z")
    latitude: float = Field(..., example=31.5204)
    longitude: float = Field(..., example=74.3587)
    altitude: float = Field(..., example=30000) # in feet
    speed: float = Field(..., example=450) # in knots


# --- Schema for the POST /ingest API ---
class IngestData(BaseModel):
    """
    This is the data model for the POST /ingest API.
    It mimics the radio signal receiver's information.
    """
    flight_id: str = Field(..., example="PK303")
    timestamp: datetime = Field(..., example="2026-01-10T09:30:00Z")
    latitude: float = Field(..., example=31.5204)
    longitude: float = Field(..., example=74.3587)
    altitude: float = Field(..., example=30000)
    speed: float = Field(..., example=450)


# --- Schemas for Creating and Storing Flights ---
class FlightBase(BaseModel):
    """
    The base details of a flight, used for creation.
    """
    flight_id: str = Field(..., example="PK303")
    airline: str = Field(..., example="PIA")
    origin: str = Field(..., example="LHE")
    destination: str = Field(..., example="JED")

class FlightCreate(FlightBase):
    """
    Model used for the POST /flights API to create a new scheduled flight.
    """
    pass # Inherits all fields from FlightBase


class FlightInDB(FlightBase):
    """
    The full flight document as stored in MongoDB.
    This is the output model for our GET API.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    status: str = Field(..., example="EN-ROUTE")
    last_update: datetime = Field(...)
    track: List[LocationPoint] = []

    class Config:
        validate_by_name = True # Pydantic v2 'allow_population_by_field_name'