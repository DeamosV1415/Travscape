from datetime import datetime
import httpx
import os
from langchain.tools import tool
from typing import Optional, Dict, Any
from agents.tools_arguments_schema import FlightSearchInput, GeneralSearch, MapSearch
import asyncio, aiohttp
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv(override=True)

#Date and Time
def get_today_str() -> str:
    """Get current date in a human-readable format."""
    # Use %#d for Windows, %-d for Unix, fallback to %d if neither is available
    try:
        return datetime.now().strftime("%a %b %#d, %Y")
    except ValueError:
        try:
            return datetime.now().strftime("%a %b %-d, %Y")
        except ValueError:
            return datetime.now().strftime("%a %b %d, %Y")


#Get City Code (Async Version)
async def get_airport_code(location):
    """This function searches the source's and destination's airport ID for a given location using the Booking.com API. The first step when searching for flights."""
    
    url = "https://google-flights2.p.rapidapi.com/api/v1/searchAirport"
    
    querystring = {"query": location, "language_code": "en-US", "country_code": "US"}
    
    headers = {
        "x-rapidapi-key": os.getenv('x-rapidapi-key'),
        "x-rapidapi-host": "google-flights2.p.rapidapi.com"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=querystring)
            response.raise_for_status()  # Raise an error for bad responses
            airport_data = response.json().get('data', [])
            
            if not airport_data:
                print("No destinations found for this query.")
                return None
            
            airport_list = airport_data[0]["list"]
            airport_code = airport_list[0]["id"]
            return airport_code
    
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


async def search_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: str,
    travel_class: str,
    adults: str,
    children: str,
    infants: str,
    show_hidden: str,
    currency: str,
    language_code: str,
    country_code: str,
    search_type: str,
) -> Dict[str, Any]:

    url = "https://google-flights2.p.rapidapi.com/api/v1/searchFlights"

    query = {
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "travel_class": travel_class,
        "adults": adults,
        "children": children,
        "infant_on_lap": infants,
        "show_hidden": show_hidden,
        "currency": currency,
        "language_code": language_code,
        "country_code": country_code,
        "search_type": search_type,
    }

    # Only include return_date if provided
    if return_date and return_date.strip():
        query["return_date"] = return_date

    headers = {
        "x-rapidapi-key": os.getenv('x-rapidapi-key'),
        "x-rapidapi-host": "google-flights2.p.rapidapi.com",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=query, timeout=15)
            resp.raise_for_status()
    except Exception as e:
        return {"error": str(e)}

    payload = resp.json()

    itineraries = payload.get("data", {}).get("itineraries", {}) or {}
    top_flights = itineraries.get("topFlights", []) or []
    other_flights = itineraries.get("otherFlights", []) or []

    # ---- Minimal LEG extractor ----
    def build_leg(leg: Dict[str, Any]) -> Dict[str, Any]:
        dep = leg.get("departure_airport") or {}
        arr = leg.get("arrival_airport") or {}
        dur = leg.get("duration") or {}

        return {
            "departure_airport_code": dep.get("airport_code"),
            "departure_airport_name": dep.get("airport_name"),
            "departure_time": dep.get("time"),
            "arrival_airport_code": arr.get("airport_code"),
            "arrival_airport_name": arr.get("airport_name"),
            "arrival_time": arr.get("time"),
            "leg_duration_text": dur.get("text"),
            "airline": leg.get("airline"),
            "airline_logo": leg.get("airline_logo"),
            "flight_number": leg.get("flight_number"),
        }

    # ---- Minimal Itinerary extractor ----
    def normalize_itinerary(itin: Dict[str, Any]) -> Dict[str, Any]:
        raw_flights = itin.get("flights")
        if raw_flights is None:
            flights_list = []
        elif isinstance(raw_flights, dict):
            flights_list = [raw_flights]
        elif isinstance(raw_flights, list):
            flights_list = raw_flights
        else:
            flights_list = []

        flights_min = [build_leg(f) for f in flights_list]

        return {
            "departure_time": itin.get("departure_time"),
            "arrival_time": itin.get("arrival_time"),
            "duration_text": (itin.get("duration") or {}).get("text"),
            "price": itin.get("price"),
            "stops": itin.get("stops"),
            "booking_token": itin.get("booking_token"),
            "flights": flights_min,
        }

    normalized_top = [normalize_itinerary(it) for it in top_flights]
    #normalized_other = [normalize_itinerary(it) for it in other_flights]

    return {
        "top_itineraries": normalized_top,
        #"other_itineraries": normalized_other,
    }


@tool(args_schema=FlightSearchInput)
async def flight_search_tool(
    departure: str,
    arrival: str,
    outbound_date: str,
    return_date: str = "",           
    travel_class: str = "ECONOMY",   
    adults: str = "1",               
    children: str = "0",             
    infants: str = "0",              
    currency: str = "INR",           
    search_type: str = "best",       
    show_hidden: str = "1",
    language_code: str = "en-US",
    country_code: str = "IN",
) -> Dict[str, Any]:
    
    """Combined tool to search for flights using the provided parameters."""
    
    # Robust date handling: ensure YYYY-MM-DD format
    # The LLM usually provides good dates, but we can add a small check if needed
    
    # Concurrent airport code lookup - 2x faster!
    departure_code, arrival_code = await asyncio.gather(
        get_airport_code(departure),
        get_airport_code(arrival)
    )
    
    print(departure_code, arrival_code)

    # Validate we got both codes
    if not departure_code or not arrival_code:
        return {"error": "Could not find airport codes for the provided locations."}
    
    # Search flights with the obtained codes
    result = await search_flights(
        departure_id=departure_code,
        arrival_id=arrival_code,
        outbound_date=outbound_date,
        return_date=return_date,
        travel_class=travel_class,
        adults=adults,
        children=children,
        infants=infants,
        show_hidden=show_hidden,
        currency=currency,
        language_code=language_code,
        country_code=country_code,
        search_type=search_type,
    )

    return result

@tool(args_schema=MapSearch)
async def maps_text_search(queries: list[str] | str):
    """Tool for maps text search. Accepts a single query string or a list of queries."""
    
    # Handle both single query and list of queries
    if isinstance(queries, str):
        queries = [queries]
    
    async def _search_single_query(session: aiohttp.ClientSession, query: str):
        """Helper function to search a single query"""
        url = "https://places.googleapis.com/v1/places:searchText"
        
        params = {"textQuery": query}
        
        headers = {
            "X-Goog-Api-Key": os.getenv("GOOGLE_API_KEY"),
            "X-Goog-FieldMask": "places.name,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.internationalPhoneNumber,places.priceLevel,places.rating,places.googleMapsUri,places.websiteUri,places.regularOpeningHours,places.googleMapsLinks"
        }
        
        try:
            async with session.post(url, json=params, headers=headers) as response:
                if response.status == 200:
                    return {
                        "query": query,
                        "success": True,
                        "data": await response.json()
                    }
                else:
                    text = await response.text()
                    print(f"Error {response.status} for query '{query}': {text}")
                    return {
                        "query": query,
                        "success": False,
                        "error": f"Status {response.status}: {text}"
                    }
        except Exception as e:
            print(f"Exception for query '{query}': {str(e)}")
            return {
                "query": query,
                "success": False,
                "error": str(e)
            }
    
    # Use a single session for all requests (more efficient)
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[_search_single_query(session, query) for query in queries], return_exceptions=True)
    
    # Return single result or list based on input
    return results[0] if len(results) == 1 else results

@tool(args_schema=GeneralSearch)
async def general_search(queries: list[str] | str):
    """Tool for general web search. Accepts a single query string or a list of queries."""

    if isinstance(queries, str):
        queries = [queries]
    
    async def _search_single_query(session: aiohttp.ClientSession, query: str):
        """Helper function to search a single query using Tavily API"""
        url = "https://api.tavily.com/search"
        
        payload = {
            "api_key": os.getenv("TAVILY_API_KEY"),
            "query": query,
            "max_results": 10,
            "topic": "general",
            "include_answer": True,
            "include_raw_content": False,
            "include_images": False
        }
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    return {
                        "query": query,
                        "success": True,
                        "data": await response.json()
                    }
                else:
                    text = await response.text()
                    print(f"Error {response.status} for query '{query}': {text}")
                    return {
                        "query": query,
                        "success": False,
                        "error": f"Status {response.status}: {text}"
                    }
        except Exception as e:
            print(f"Exception for query '{query}': {str(e)}")
            return {
                "query": query,
                "success": False,
                "error": str(e)
            }
    
    # Use a single session for all requests (more efficient)
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[_search_single_query(session, query) for query in queries],
            return_exceptions=False
        )
    
    # Return single result or list based on input
    return results[0] if len(results) == 1 else results