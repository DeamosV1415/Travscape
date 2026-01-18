from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Union

#Planner
class TimeBlock(BaseModel):
    period: Literal["Morning", "Afternoon", "Evening"]=Field(description="The time block of the day.")
    activity_type: str=Field(description="The tupe of activity. Eg: sightseeing/dining/activity/transit/relaxation")
    priority: Literal["must_do", "nice_to_have", "flexible"]=Field(description="Priority level of the activity.")
    requirements: str=Field(description="Detailed description of what to look for.") 

class DayPlan(BaseModel):
    day_number: int
    date: str
    location: str=Field(description="City/area for this day.")
    theme: str=Field(description="Overall theme or focus for the day. Eg: Exploration, Relaxation, Adventure.")
    time_blocks: List[TimeBlock]

class SearchCriteria(BaseModel):
    location: str = Field(default="", description="Specific area or location to search in")
    features: List[str] = Field(default_factory=list, description="List of required features")
    price_range: str = Field(default="", description="Budget indicator")
    keywords: str = Field(default="", description="Additional search keywords")
    category: str = Field(default="", description="Specific category")

class Constraints(BaseModel):
    pace: str = Field(default="moderate", description="Trip pace: relaxed/moderate/packed")
    interests: List[str] = Field(default_factory=list, description="List of interests")
    avoid: List[str] = Field(default_factory=list, description="Things to avoid")

class BudgetInfo(BaseModel):
    total: float = Field(default=0, description="Total budget")
    currency: str = Field(default="USD", description="Currency code")
    trip_type: Literal["budget", "mid-range", "luxury"] = Field(default="mid-range", description="Type of trip")

class SearchTask(BaseModel):
    task_id: str=Field(description="Unique ID of the task. Eg: flight_search_1, hotel_search_1, flight_search_2, general_search_1, maps_text_search_1...")
    search_type: str = Field(description="Type of search. e.g., transportation, accomodation, general_info, destination_research, restaurant, attraction, activity")
    criteria: SearchCriteria=Field(description="Search parameters")
    for_day: int=Field(description="The day number in the trip plan this search is for.")
    for_time_block: str = Field(description="The time block associated with this search. e.g., Morning, Afternoon, Evening, or empty string for exploratory.")
    priority: Literal["high", "medium", "low"]=Field(description="Priority level of the search task.")

class TripPlan(BaseModel):
    trip_summary: str=Field(default="", description="Overview of the trip plan")  
    daily_structure: List[DayPlan]=Field(default_factory=list, description="The day-wise structure of the trip")
    search_tasks: List[SearchTask]=Field(default_factory=list, description="Any searches that the orchestrator will need to run about some places or preferences")
    constraints: Constraints=Field(default_factory=Constraints, description="Rules and preferences to follow while planning")
    estimated_budget: BudgetInfo=Field(default_factory= BudgetInfo, description="Budget breakdown if mentioned")

class PlannerOutput(BaseModel):
    needs_clarification: bool = Field(default=False, description="True if the planner needs clarification from the user. False otherwise.")
    clarification_question: Optional[str] = Field(default=None, description="The clarification question that the planner needs to ask the user. None, if no clarification is needed.")
    plan: Optional[TripPlan] = Field(default=None, description="The travel plan created by the planner. Empty list if clarification is needed.")