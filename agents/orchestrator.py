from agents.GlobalState import AgentState
from agents.orchestrator_output import OrchestratorOutput
from typing import Literal
import json
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from agents.prompts import orchestrator_message
from agents.utils import get_today_str, flight_search_tool, maps_text_search, general_search
from langgraph.types import Command

def should_try_tools(state: AgentState) -> bool:
    """
    Determine if we should try calling tools based on state.
    
    Returns True if:
    - We have pending tasks to execute
    - We just received tool results (might need to continue)
    - User made a simple search request (no trip plan needed)
    
    Returns False if:
    - We need to route to planner first
    - We're in casual conversation
    - We clearly need clarification
    """
    messages = state.get("messages", [])
    pending_tasks = state.get("pending_tasks", [])
    need_trip_plan = state.get("need_trip_plan", False)
    trip_plan = state.get("trip_plan", {})
    user_request = state.get("user_request", [])
    
    # If we need a trip plan and don't have one, don't try tools yet
    # (we need to route to planner first)
    if need_trip_plan and not trip_plan:
        return False
    
    # If we have pending tasks, we should try tools
    if pending_tasks:
        return True
    
    # If last message is a tool result, we might need to continue
    if messages and isinstance(messages[-1], ToolMessage):
        return True
    
    # If user made a simple search request (no trip plan needed)
    if user_request and not need_trip_plan:
        return True
    
    # Otherwise, don't try tools (use structured output for routing)
    return False


def _summarize_messages_for_prompt(messages: list, max_messages: int = 8) -> str:
    """
    Create a compact summary of recent messages for the orchestrator prompt.
    Instead of dumping the entire message list (which includes massive tool results),
    we keep only recent messages and summarize tool results to just key data.
    """
    if not messages:
        return "No messages yet."
    
    # Take only the last N messages
    recent = messages[-max_messages:]
    summary_parts = []
    
    for msg in recent:
        if isinstance(msg, HumanMessage):
            summary_parts.append(f"User: {msg.content[:300]}")
        elif isinstance(msg, AIMessage):
            # Skip tool-calling messages with no content
            if not msg.content and hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_names = [tc.get("name", "unknown") for tc in msg.tool_calls]
                summary_parts.append(f"Assistant: [Called tools: {', '.join(tool_names)}]")
            elif msg.content:
                summary_parts.append(f"Assistant: {msg.content[:300]}")
        elif isinstance(msg, ToolMessage):
            # Summarize tool results — only key info, not full JSON
            tool_name = msg.name if hasattr(msg, "name") else "unknown"
            try:
                data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                if isinstance(data, dict):
                    if "top_itineraries" in data:
                        flights = data["top_itineraries"]
                        flight_summary = [f"₹{f.get('price',0)} ({f.get('duration_text','?')})" for f in flights[:3]]
                        summary_parts.append(f"Tool ({tool_name}): Found {len(flights)} flights: {', '.join(flight_summary)}")
                    elif "places" in data.get("data", {}):
                        places = data["data"]["places"]
                        place_names = [p.get("displayName", {}).get("text", "?") for p in places[:5]]
                        summary_parts.append(f"Tool ({tool_name}): Found {len(places)} places: {', '.join(place_names)}")
                    elif "success" in data:
                        if data.get("success") and "data" in data:
                            inner = data["data"]
                            if isinstance(inner, dict) and "places" in inner:
                                places = inner["places"]
                                place_names = [p.get("displayName", {}).get("text", "?") for p in places[:5]]
                                summary_parts.append(f"Tool ({tool_name}): Found {len(places)} places: {', '.join(place_names)}")
                            else:
                                summary_parts.append(f"Tool ({tool_name}): Results received (success)")
                        else:
                            summary_parts.append(f"Tool ({tool_name}): {data.get('error', 'Failed')}")
                    else:
                        summary_parts.append(f"Tool ({tool_name}): Results received")
                else:
                    summary_parts.append(f"Tool ({tool_name}): Results received")
            except (json.JSONDecodeError, TypeError):
                summary_parts.append(f"Tool ({tool_name}): {msg.content[:150]}")
        elif isinstance(msg, SystemMessage):
            pass  # Skip system messages in summary
    
    return "\n".join(summary_parts)


def _get_completed_tool_queries(messages: list) -> set:
    """
    Extract all tool queries that have already been executed,
    so we can detect and prevent duplicate tool calls.
    """
    completed_queries = set()
    for msg in messages:
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                if isinstance(data, dict) and "query" in data:
                    completed_queries.add(data["query"].lower().strip())
            except (json.JSONDecodeError, TypeError):
                pass
    return completed_queries


async def orchestrator_node(state: AgentState) -> AgentState:
    """
    Agentic orchestrator node with optimized single-LLM-call logic
    
    Strategy:
    1. Check state to decide if we should try tools
    2. If yes: Call llm_with_tools
       - If tool_calls generated: Return them
       - If not: Fall through to structured output
    3. If no: Call llm_with_structured_output directly
    
    This ensures we only call the LLM once in most cases.
    """
    orch = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2
    )
    
    messages = state.get("messages", [])
    new_iteration = state.get("iteration", 0) + 1
    max_iterations = state.get("max_iterations", 8)
    pending_tasks = state.get("pending_tasks", []).copy()
    completed_tasks = state.get("completed_tasks", []).copy()

    # ============================================================
    # FIX 1: Pop ALL completed tasks when multiple tools return
    # When the orchestrator calls 3 tools in parallel, ToolNode
    # returns 3 ToolMessages. We must mark ALL corresponding tasks
    # as completed, not just one.
    # ============================================================
    
    # Count how many consecutive ToolMessages are at the end of messages
    tool_result_count = 0
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            tool_result_count += 1
        else:
            break
    
    # Pop that many tasks from pending (or all remaining, whichever is smaller)
    tasks_to_pop = min(tool_result_count, len(pending_tasks))
    for _ in range(tasks_to_pop):
        if pending_tasks:
            task_done = pending_tasks.pop(0)
            if task_done not in completed_tasks:
                completed_tasks.append(task_done)

    # ============================================================
    # FIX 2: Hard iteration guard — force completion
    # ============================================================
    
    if new_iteration > max_iterations:
        print(f"[Orchestrator] Hit max iterations ({max_iterations}), forcing completion.")
        
        # Build a best-effort summary from whatever tool results we have
        summary_parts = []
        for msg in reversed(messages[-20:]):
            if isinstance(msg, ToolMessage):
                try:
                    data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                    if isinstance(data, dict):
                        if "top_itineraries" in data:
                            summary_parts.append("Flight results found.")
                        elif "data" in data and isinstance(data["data"], dict) and "places" in data["data"]:
                            places = data["data"]["places"]
                            names = [p.get("displayName", {}).get("text", "?") for p in places[:5]]
                            summary_parts.append(f"Places found: {', '.join(names)}")
                        elif "success" in data and data.get("data") and "places" in data.get("data", {}):
                            places = data["data"]["places"]
                            names = [p.get("displayName", {}).get("text", "?") for p in places[:5]]
                            summary_parts.append(f"Places found: {', '.join(names)}")
                except (json.JSONDecodeError, TypeError):
                    pass
        
        forced_response = "Here's what I found based on my research:\n\n" + "\n".join(summary_parts) if summary_parts else "I've gathered some information for your trip. Let me know if you need anything specific!"
        
        return {
            "messages": [AIMessage(content=forced_response)],
            "iteration": new_iteration,
            "pending_tasks": [],
            "completed_tasks": completed_tasks,
            "needs_planner": False,
        }

    # ============================================================
    # FIX 3: Truncate chat history for the prompt
    # ============================================================

    # Extract recent tool results (compact format for prompt)
    recent_tool_results = []
    for msg in reversed(messages[-10:]):
        if isinstance(msg, ToolMessage):
            recent_tool_results.append({
                "tool": msg.name if hasattr(msg, "name") else "unknown",
                "result": msg.content[:500]
            })
    recent_tool_results = recent_tool_results[:3]

    # Build context for orchestrator — use summarized history, not raw dump
    chat_summary = _summarize_messages_for_prompt(messages)
    
    system_message = orchestrator_message.format(
        date=get_today_str(),
        chat_history=chat_summary,
        user_request=state.get("user_request", []),
        need_trip_plan=state.get("need_trip_plan", False),
        trip_plan=state.get("trip_plan", {}),
        tool_results=recent_tool_results,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        iteration=new_iteration,
        max_iterations=max_iterations
    )
    
    # ============================================================
    # DECISION POINT: Should we try tools?
    # ============================================================
    
    if should_try_tools(state):
        # ========================================================
        # PATH A: Try to call tools
        # ========================================================
        
        tools = [maps_text_search, general_search, flight_search_tool]
        orch_with_tools = orch.bind_tools(tools)
        
        response = await orch_with_tools.ainvoke([SystemMessage(content=system_message)])
        
        # If LLM generated tool_calls, check for duplicates before returning
        if hasattr(response, "tool_calls") and response.tool_calls:
            
            # FIX 4: Deduplicate tool calls against already-completed queries
            completed_queries = _get_completed_tool_queries(messages)
            filtered_tool_calls = []
            
            for tc in response.tool_calls:
                args = tc.get("args", {})
                # Check map/general search queries
                queries = args.get("queries", [])
                if isinstance(queries, str):
                    queries = [queries]
                
                # If ALL queries in this tool call are already completed, skip it
                if queries and all(q.lower().strip() in completed_queries for q in queries):
                    print(f"[Orchestrator] Skipping duplicate tool call: {tc.get('name')} with {queries}")
                    continue
                
                filtered_tool_calls.append(tc)
            
            if filtered_tool_calls:
                # Rebuild the response with only non-duplicate tool calls
                response.tool_calls = filtered_tool_calls
                return {
                    "messages": [response],
                    "iteration": new_iteration,
                    "pending_tasks": pending_tasks,
                    "completed_tasks": completed_tasks,
                    "needs_planner": False,  # FIX 5: Reset flag
                }
            
            # All tool calls were duplicates — fall through to structured output
            print("[Orchestrator] All tool calls were duplicates, falling through to structured output.")
    
    # ============================================================
    # PATH B: Use structured output for routing decision
    # ============================================================
    
    structured_orch = orch.with_structured_output(OrchestratorOutput)
    decision: OrchestratorOutput = await structured_orch.ainvoke([SystemMessage(content=system_message)])
    
    # Handle different actions
    if decision.action == "ROUTE_TO_PLANNER":
        return {
            "messages": [AIMessage(content="Let me create a detailed trip plan for you...")],
            "iteration": new_iteration,
            "needs_planner": True,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks
        }
    
    elif decision.action == "ROUTE_TO_CHATBOT":
        return {
            "messages": [AIMessage(content=decision.clarification_message or "I need some clarification.")],
            "iteration": new_iteration,
            "needs_clarification": True,
            "needs_planner": False,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks
        }
    
    elif decision.action == "COMPLETE":
        final_text = decision.final_response or "I've completed the tasks."
        
        # Check for flight data in recent tool messages and inject structured data
        for msg in reversed(messages[-10:]):
            if isinstance(msg, ToolMessage):
                try:
                    tool_data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                    if isinstance(tool_data, dict) and "top_itineraries" in tool_data:
                        flight_json = json.dumps(tool_data["top_itineraries"])
                        final_text += f"\n[FLIGHTS_START]{flight_json}[FLIGHTS_END]"
                        break
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return {
            "messages": [AIMessage(content=final_text)],
            "iteration": new_iteration,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "needs_planner": False,
        }
    
    # Fallback
    return {
        "messages": [AIMessage(content="I'm not sure what to do next.")],
        "iteration": new_iteration,
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "needs_planner": False,
    }