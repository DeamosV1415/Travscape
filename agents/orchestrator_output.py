from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

# ==================== ORCHESTRATOR SCHEMAS ====================

# class ToolCall(BaseModel):
#     """Individual tool call decision"""
#     tool_name: Literal["Flight Search", "Maps Text Search", "General Search"]
#     tool_input: Dict[str, Any] = Field(description="Parameters for the tool")

class OrchestratorOutput(BaseModel):
    """Orchestrator's ReAct decision output"""
    thought: str = Field(description="ReAct reasoning about current state and next action")
    
    action: Literal["ROUTE_TO_CHATBOT", "COMPLETE"] = Field(
        description="Next action to take"
    )
    
    # Conditional fields based on action
    # tool_calls: Optional[List[ToolCall]] = Field(
    #     default=None, 
    #     description="Tool calls to execute (only for CALL_TOOL action)"
    # )

    clarification_message: Optional[str] = Field(
        default=None,
        description="Message to ask user (only for ROUTE_TO_CHATBOT action)"
    )

    final_response: Optional[str] = Field(
        default=None,
        description="Final formatted response (only for COMPLETE action)"
    )
    
    # should_continue: bool = Field(description="Whether to continue ReAct loop after this action")
    # status_message: str = Field(description="User-friendly update about current progress")
    
    # Task tracking
    pending_tasks: List[str] = Field(default_factory=list, description="Task IDs still to execute")
    completed_tasks: List[str] = Field(default_factory=list, description="Task IDs completed")
    