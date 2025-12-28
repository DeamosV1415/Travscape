from agents.GlobalState import AgentState
from agents.orchestrator_output import OrchestratorOutput
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from agents.prompts import orchestrator_message
from agents.utils import get_today_str, flight_search_tool, maps_text_search, general_search
from langgraph.types import Command

async def orchestrator_node(state: AgentState) -> AgentState:
    """
    Orchestrator node - ReAct agent that coordinates the workflow.
    
    Decides to:
    - Call tools for search tasks
    - Route to planner for new trip requests
    - Route to chatbot for clarification
    - Complete when all tasks done
    """
    orch = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2
    )
    
    # Bind tools to LLM so it can generate tool calls
    tools = [flight_search_tool, maps_text_search, general_search]
    orch_with_tools = orch.bind_tools(tools)
    
    # Build context for orchestrator
    system_message = orchestrator_message.format(
        date=get_today_str(),
        user_message=state["messages"][-1].content if state["messages"] else "",
        chat_history=state.get("messages", []),
        user_request=state.get("user_request", []),
        trip_plan=state.get("trip_plan", {}),
        tool_results=state.get("tool_results", []),
        pending_tasks=state.get("pending_tasks", []),
        completed_tasks=state.get("completed_tasks", []),
        iteration=state.get("iteration", 0),
        max_iterations=state.get("max_iterations", 10)
    )
    
    new_iteration = state.get("iteration", 0) + 1

    # CONDITION 1: Need trip plan? Route to planner FIRST
    if state.get("need_trip_plan") and not state.get("trip_plan"):
        return Command(
            update={
                "iteration": new_iteration,
                "next_action": "planner",
                "messages": [AIMessage(content="Routing to planner to create trip plan")]
            }
        )
    
    # CONDITION 2.5: Just returned from tools? Process result and decide next action
    messages = state.get("messages", [])
    if messages and isinstance(messages[-1], ToolMessage):
        structured_orch = orch.with_structured_output(OrchestratorOutput)
        decision: OrchestratorOutput = await structured_orch.ainvoke([SystemMessage(content=system_message)])
        
        # Check if LLM decided we're done after processing tool results
        if decision.action == "COMPLETE":
            return Command(
                update={
                    "iteration": new_iteration,
                    "conversation_state": "complete",
                    "next_action": "end",
                    "messages": [AIMessage(content=decision.final_response)],
                    "pending_tasks": decision.pending_tasks,
                    "completed_tasks": decision.completed_tasks
                }
            )
        elif decision.action == "ROUTE_TO_CHATBOT":
            return Command(
                update={
                    "iteration": new_iteration,
                    "needs_user_clarification": True,
                    "clarification_question": decision.clarification_message,
                    "next_action": "end",
                    "messages": [AIMessage(content=decision.clarification_message)],
                    "pending_tasks": decision.pending_tasks,
                    "completed_tasks": decision.completed_tasks
                }
            )
        # Otherwise, continue to CONDITION 2 to potentially call more tools
        
    # CONDITION 2: Simple search (user_request exists but no trip plan needed)
    # OR have pending tasks from planner
    if (state.get("user_request") and not state.get("need_trip_plan")) or state.get("pending_tasks"):
        response = await orch_with_tools.ainvoke([SystemMessage(content=system_message)])
        
        if response.tool_calls:
            return Command(
                update={
                    "iteration": new_iteration,
                    "next_action": "tools",
                    "messages": [response]
                }
            )
        else:
            # No tool calls generated - LLM decided work is done
            # Fall through to CONDITION 3 for structured decision
            pass
    # CONDITION 3: No tools needed, get routing decision
    structured_orch = orch.with_structured_output(OrchestratorOutput)
    decision: OrchestratorOutput = await structured_orch.ainvoke([SystemMessage(content=system_message)])
    
    if decision.action == "ROUTE_TO_CHATBOT":
        return Command(
          update= {
            "iteration": new_iteration,
            "needs_user_clarification": True,
            "clarification_question": decision.clarification_message,
            "next_action": "end",
            "messages": [AIMessage(content=decision.clarification_message)],
            "pending_tasks": decision.pending_tasks,
            "completed_tasks": decision.completed_tasks
          }
        )
    
    elif decision.action == "COMPLETE":
        return Command(
          update= {
            "iteration": new_iteration,
            "conversation_state": "complete",
            "next_action": "end",
            "messages": [AIMessage(content=decision.final_response)],
            "pending_tasks": decision.pending_tasks,
            "completed_tasks": decision.completed_tasks
          }
        )
    
    else:
        # Default: end
        return Command(
          update= {
            "iteration": new_iteration,
            "next_action": "end"
          }
        )