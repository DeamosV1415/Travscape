from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

# ==================== ORCHESTRATOR SCHEMAS ====================

class OrchestratorOutput(BaseModel):
    """Orchestrator's ReAct decision output"""

    thought: str = Field(description="ReAct reasoning about current state and next action")
    
    action: Literal["ROUTE_TO_PLANNER", "ROUTE_TO_CHATBOT", "COMPLETE"] = Field(
        description="Next action to take"
    )

    clarification_message: Optional[str] = Field(
        default=None,
        description="Message to ask user (only for ROUTE_TO_CHATBOT action)"
    )

    final_response: Optional[str] = Field(
        default=None,
        description="Final formatted response (only for COMPLETE action)"
    )