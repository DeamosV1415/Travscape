from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

# State
class AgentState(TypedDict):
  messages: Annotated[list, add_messages]
  user_request: list
  trip_plan: list
