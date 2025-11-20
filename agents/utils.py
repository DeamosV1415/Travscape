from datetime import datetime
import httpx
import os
from langchain.tools import tool
from typing import Optional, Dict, Any

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


#Get City Code
def get_airport_code(location):
  """This function searches the source's and destination's airport ID for a given location using the Booking.com API. The first step when searching for flights."""

  url = "https://booking-com15.p.rapidapi.com/api/v1/flights/searchDestination"

  querystring = {"query":location}

  headers = {
    "x-rapidapi-key": os.getenv('x-rapidapi-key'),
    "x-rapidapi-host": "booking-com15.p.rapidapi.com"
  }
  try:
    response = httpx.get(url, headers=headers, params=querystring)
    response.raise_for_status()  # Raise an error for bad responses
    airport_code = response.json().get('data', [])
    
    if not airport_code:
        print("No destinations found for this query.")
        airport_details = []

    airport_details = [dest["code"] for dest in airport_code] #Saves all airport IDs for the given location
  
  except httpx.HTTPStatusError as e:
    print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
  except httpx.RequestError as e:
    print(f"Request error occurred: {e}") 
  
  return airport_details

def search_flights(
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
        resp = httpx.get(url, headers=headers, params=query, timeout=15)
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
    normalized_other = [normalize_itinerary(it) for it in other_flights]

    return {
        "top_itineraries": normalized_top,
        "other_itineraries": normalized_other,
    }

#@tool
def flight_search_tool(
    departure: str,
    arrival: str,
    outbound_date: str,
    return_date: str = "",
    travel_class: str = "Economy",
    adults: str = "1",
    children: str = "0",
    infants: str = "0",
    show_hidden: str = "1",
    currency: str = "INR",
    language_code: str = "en-US",
    country_code: str = "IN",
    search_type: str = "best",
) -> Dict[str, Any]:
    
    """Combined tool to search for flights using the provided parameters."""
    departure_code = get_airport_code(departure)
    arrival_code = get_airport_code(arrival)
    print(departure_code, arrival_code)

    if not departure_code or arrival_code:
        return {"error": "Could not find airport codes for the provided locations."}
    
    return search_flights(
        departure_id=departure_code[1],
        arrival_id=arrival_code[1],
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