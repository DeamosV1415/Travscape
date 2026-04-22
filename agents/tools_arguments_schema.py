from pydantic import BaseModel, Field
from typing import Literal

class FlightSearchInput(BaseModel):
    """Input for flight search tool"""
    departure: str = Field(description="Departure city name (e.g. 'Delhi', 'New York'). Do NOT use airport codes like DEL or JFK.")
    arrival: str = Field(description="Arrival city name (e.g. 'San Francisco', 'London'). Do NOT use airport codes like SFO or LHR.")
    outbound_date: str = Field(description="Departure date in YYYY-MM-DD format")
    return_date: str = Field(default="", description="Return date in YYYY-MM-DD format (empty for one-way)")
    travel_class: Literal["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"] = Field(default="ECONOMY", description="Cabin class: economy, premium_economy, business, first")
    adults: int = Field(default=1, description="Number of adults")
    children: int = Field(default=0, description="Number of children")
    infants: int = Field(default=0, description="Number of infants")
    currency: str = Field(default="INR", description="Currency code (e.g., INR, USD)")
    search_type: Literal["best", "cheap"] = Field(default="best", description="Search type: best, cheap")

class GeneralSearch(BaseModel):
    """"Input for the general search tool"""
    queries: list[str] = Field(default_factory=list, description="Search query")

class MapSearch(BaseModel):
    """Input for the map search tool"""
    queries: list[str] = Field(default_factory=list, description="Map Text Search query")