from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
import operator

# State
class AgentState(TypedDict, total=False):
  messages: Annotated[list, add_messages]
  user_request: list
  need_trip_plan: bool
  needs_clarification: bool
  route_to_orch: bool
  needs_planner: bool
  trip_plan: dict
  orchestrator_output: dict
  next_action: str
  pending_tasks: list
  completed_tasks: list
  iteration: int        # defaults to 0 when absent
  max_iterations: int   # defaults to 8 via .get() fallbacks in orchestrator/routing

