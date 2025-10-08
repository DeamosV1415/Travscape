from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

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

class SearchTask(BaseModel):
    task_id: str=Field(description="Unique ID of the task. Eg: search_1, search_2...")
    search_type: Literal["attraction", "restaurant", "hotel", "general_info", "destination_research"]=Field(description="Type of search.")
    criteria: Dict[str, Any]=Field(description="Dictionary of search parameters specific to the search_type.")
    for_day: int=Field(description="The day number in the trip plan this search is for.")
    for_time_block: Literal["Morning", "Afternoon", "Evening"]=Field(description="The time block accociated with this search.")
    priority: Literal["high", "medium", "low"]=Field(description="Priority level of the search task.")

class trip_plan(BaseModel):
    trip_summary: Optional[str]=Field(None, description="Overview of the trip plan")  
    daily_structure: List[DayPlan]=Field([], description="The day-wise structure of the trip")
    search_tasks: List[SearchTask]=Field([], description="Any searches that the orchestrator will need to run about some places or preferences")
    constraints: Dict[str, Any]=Field({}, description="Rules and preferences to follow while planning")
    estimated_budget: Optional[dict]=Field(None, description="Budget breakdown if mentioned")

class PlannerOutput(BaseModel):
    need_clarification: bool = Field(False, description="True if the planner needs clarification from the user. False otherwise.")
    clarification_question: Optional[str] = Field(None, description="The clarification question that the planner needs to ask the user. None, if no clarification is needed.")
    plan: Optional[trip_plan] = Field(None, description="The travel plan created by the planner. Empty list if clarification is needed.")


