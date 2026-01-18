from agents.GlobalState import AgentState
from agents.orchestrator_output import OrchestratorOutput
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
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
        model="gpt-4.1-mini",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2
    )
    
    # Bind tools to LLM so it can generate tool calls
    tools = [flight_search_tool, maps_text_search, general_search]
    orch_with_tools = orch.bind_tools(tools)
    
    # Extract tool results from messages for the prompt
    all_tool_results = state.get("tool_results", [])
    for msg in state.get("messages", []):
        if isinstance(msg, ToolMessage):
            all_tool_results.append(msg.content)

    # Build context for orchestrator
    system_message = orchestrator_message.format(
        date=get_today_str(),
        user_message=state["messages"][-1].content if state["messages"] else "",
        chat_history=state.get("messages", []),
        user_request=state.get("user_request", []),
        trip_plan=state.get("trip_plan", {}),
        tool_results=all_tool_results,
        pending_tasks=state.get("pending_tasks", []),
        completed_tasks=state.get("completed_tasks", []),
        iteration=state.get("iteration", 0),
        max_iterations=state.get("max_iterations", 10)
    )
    
    new_iteration = state.get("iteration", 0) + 1
    pending_tasks = state.get("pending_tasks", [])
    completed_tasks = state.get("completed_tasks", [])

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
        # Update pending and completed tasks based on the tool that just ran
        last_tool_msg = messages[-1]
        tool_call_id = last_tool_msg.tool_call_id
        
        # Find which task this tool call belonged to
        # We look at the AI message before the tool message to find the tool call
        pending_tasks = state.get("pending_tasks", [])
        completed_tasks = state.get("completed_tasks", [])
        
        # Simple heuristic: if we just got a tool result, the first pending task is likely completed
        # In a more complex system, we'd map tool_call_id to task_id
        if pending_tasks:
            task_done = pending_tasks.pop(0)
            if task_done not in completed_tasks:
                completed_tasks.append(task_done)

        structured_orch = orch.with_structured_output(OrchestratorOutput, method="function_calling")
        decision: OrchestratorOutput = await structured_orch.ainvoke([SystemMessage(content=system_message)])
        
        # Check if LLM decided we're done after processing tool results
        if decision.action == "COMPLETE":
            # If we just finished a research task and still need a trip plan, route back to planner
            if state.get("need_trip_plan") and not state.get("trip_plan"):
                 return Command(
                    update={
                        "iteration": new_iteration,
                        "next_action": "planner",
                        "pending_tasks": pending_tasks,
                        "completed_tasks": completed_tasks
                    }
                )

            return Command(
                update={
                    "iteration": new_iteration,
                    "conversation_state": "complete",
                    "next_action": "end",
                    "messages": [AIMessage(content=decision.final_response if decision.final_response else "I've completed the tasks.")],
                    "pending_tasks": pending_tasks,
                    "completed_tasks": completed_tasks
                }
            )
        elif decision.action == "ROUTE_TO_CHATBOT":
            return Command(
                update={
                    "iteration": new_iteration,
                    "needs_user_clarification": True,
                    "clarification_question": decision.clarification_message,
                    "next_action": "end",
                    "messages": [AIMessage(content=decision.clarification_message if decision.clarification_message else "I need some clarification.")],
                    "pending_tasks": pending_tasks,
                    "completed_tasks": completed_tasks
                }
            )
        # Otherwise, continue to CONDITION 2 to potentially call more tools
        
    # CONDITION 2: Simple search (user_request exists but no trip plan needed)
    # OR have pending tasks from planner
    # OR user is asking to "check again" or "try another"
    is_follow_up = any(word in state["messages"][-1].content.lower() for word in ["check", "try", "again", "another", "search"]) if state["messages"] else False
    
    if (state.get("user_request") and not state.get("need_trip_plan")) or state.get("pending_tasks") or is_follow_up:
        response = await orch_with_tools.ainvoke([SystemMessage(content=system_message)])
        
        if response.tool_calls:
            return Command(
                update={
                    "iteration": new_iteration,
                    "next_action": "tools"
                }
            )
        elif is_follow_up and not response.tool_calls:
            # If it's a follow-up but no tool calls were generated, we might need to force a tool call or handle it
            pass
    # CONDITION 3: No tools needed, get routing decision
    structured_orch = orch.with_structured_output(OrchestratorOutput, method="function_calling")
    decision: OrchestratorOutput = await structured_orch.ainvoke([SystemMessage(content=system_message)])
    
    if decision.action == "ROUTE_TO_CHATBOT":
        return Command(
          update= {
            "iteration": new_iteration,
            "needs_user_clarification": True,
            "clarification_question": decision.clarification_message,
            "next_action": "end",
            "messages": [AIMessage(content=decision.clarification_message if decision.clarification_message else "I need some clarification.")],
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks
          }
        )
    
    elif decision.action == "COMPLETE":
        return Command(
          update= {
            "iteration": new_iteration,
            "conversation_state": "complete",
            "next_action": "end",
            "messages": [AIMessage(content=decision.final_response if decision.final_response else "I've completed the tasks.")],
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks
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