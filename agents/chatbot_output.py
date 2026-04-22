from pydantic import BaseModel, Field
from typing import List, Optional

# Structured Outputs
class TripRequest(BaseModel):
    destination: Optional[str] = None
    dates: Optional[str] = None
    travelers: Optional[int] = None
    budget: Optional[str] = None
    purpose: Optional[str] = None
    preferences: Optional[str] = None

class chatbot_output(BaseModel):
  user_request:List[TripRequest]= Field(default_factory=list, description="List of all the requests that the user has. Also includes the details of the trip.")
  needs_clarification: bool = Field(False, description="True if the chatbot needs clarification from the user about any of the missing field in the user_request. False otherwise.")
  clarification_question: Optional[str] = Field(None, description="The clarification question that the chatbot needs to ask the user. None, if no clarification is needed.")
  chatbot_reply: str = Field(default="", description="The chatbot's response to the user.")
  need_trip_plan: bool = Field(False, description="True if the user needs to plan a trip. False otherwise.")
  route_to_orch: bool = Field(False, description="True if the agent should proceed to the orchestrator after getting all the details. False if it should wait for user clarification.")
