from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Literal

# =====================================================
# ORCHESTRATOR REACT DECISION SCHEMA
# =====================================================

class OrchestratorDecision(BaseModel):
    """
    Orchestrator's ReAct decision following the Reason → Act → Observe pattern.
    This schema captures the orchestrator's thought process and next action.
    """
    model_config = ConfigDict(extra='forbid')
    
    thought: str = Field(
        description="The orchestrator's reasoning about the current state. Explain what information you have, what you need, and why you're taking this action. (2-3 sentences)"
    )
    
    action: Literal[
        "CALL_TOOL",
        "ROUTE_TO_PLANNER",
        "ROUTE_TO_ITINERARY",
        "ROUTE_TO_HUMAN",
        "RESPOND"
    ] = Field(
        description="The action to take based on reasoning. CALL_TOOL for searches, ROUTE_TO_* for agent routing, RESPOND for direct user communication."
    )
    
    action_input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input data for the action. Structure varies by action type: tool parameters, trip_details, messages, etc."
    )
    
    should_continue: bool = Field(
        default=True,
        description="Whether the ReAct loop should continue after this action. true = keep looping, false = end turn and wait"
    )
    
    status_message: str = Field(
        description="User-friendly message about what's currently happening. Keep users informed of progress."
    )
    
    pending_tasks: List[str] = Field(
        default_factory=list,
        description="List of search task IDs that still need to be executed"
    )
    
    completed_tasks: List[str] = Field(
        default_factory=list,
        description="List of search task IDs that have been completed with results"
    )
    
    observation_notes: str = Field(
        description="What you expect to observe after this action executes. This guides the next reasoning step."
    )


