
from datetime import datetime
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from pydantic import BaseModel, Field


# State
class AgentState(TypedDict):
  messages: Annotated[list, add_messages]
  need_clarification: bool
  user_request: list

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
  need_clarification: bool = Field(False, description="True if the chatbot needs clarification from the user. False otherwise.")
  clarification_question: Optional[str] = Field(None, description="The clarification question that the chatbot needs to ask the user. None, if no clarification is needed.")
  chatbot_reply: Optional[str] = Field(None, description="The chatbot's response to the user.")
