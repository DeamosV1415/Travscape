from agents.GlobalState import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from agents.chatbot import chatbot_node
from agents.planner import planner_node
from agents.orchestrator import orchestrator_node
from agents.utils import flight_search_tool, maps_text_search, general_search
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from typing import Literal

def route_after_chatbot(state: AgentState) -> Literal["orchestrator", "__end__"]:
    """Route from chatbot to orchestrator or end"""
    if state.get("route_to_orch"):
        return "orchestrator"
    else:
        return "__end__"

def route_after_orchestrator(state: AgentState) -> Literal["tools", "planner", "__end__"]:
    """
    Route based on orchestrator's output
    
    Priority order:
    0. If iteration exceeded max → force end (circuit breaker)
    1. If orchestrator called tools → go to tools
    2. If orchestrator needs planner → go to planner
    3. Otherwise → end (orchestrator provided final response or asked for clarification)
    """
    # CIRCUIT BREAKER: Force end if we've iterated too many times
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 8)
    if iteration >= max_iterations:
        return "__end__"
    
    messages = state.get("messages", [])
    
    # Check the last message from orchestrator
    if not messages:
        return "__end__"
    
    last_message = messages[-1]
    
    # PRIORITY 1: If the last message has tool_calls, route to tools
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # PRIORITY 2: If orchestrator signaled it needs planner, route to planner
    if state.get("needs_planner"):
        return "planner"
    
    # PRIORITY 3: Otherwise, we're done (either complete or needs clarification)
    # If needs_clarification is True, the chatbot will handle it on next user message
    return "__end__"

def route_after_planner(state: AgentState) -> Literal["chatbot", "orchestrator"]:
    """Route from planner back to orchestrator or chatbot"""
    if state.get("needs_clarification"):
        return "chatbot"
    else:
        return "orchestrator"

def create_graph():
    """
    Build and compile the complete orchestrator graph.
    
    Returns:
        Compiled LangGraph application with checkpointing
    """
    # Initialize graph with state schema
    workflow = StateGraph(AgentState)
    
    # Create tool node with all available tools
    tools = [flight_search_tool, maps_text_search, general_search]
    tool_node = ToolNode(tools)
    
    # Add all nodes
    workflow.add_node("chatbot", chatbot_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("tools", tool_node)
    
    # Set entry point - all conversations start with chatbot
    workflow.add_edge(START, "chatbot")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "chatbot",
        route_after_chatbot,
        {
            "orchestrator": "orchestrator",
            "__end__": END
        }
    )
    
    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "tools": "tools",
            "planner": "planner",
            "__end__": END
        }
    )
    
    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "chatbot": "chatbot",
            "orchestrator": "orchestrator"
        }
    )
    
    # Tools always route back to orchestrator
    workflow.add_edge("tools", "orchestrator")

    memory = InMemorySaver()
    graph = workflow.compile(checkpointer=memory)

    return graph