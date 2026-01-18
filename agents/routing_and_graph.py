from agents.GlobalState import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from agents.chatbot import chatbot_node
from agents.planner import planner_node
from agents.orchestrator import orchestrator_node
from agents.utils import flight_search_tool, maps_text_search, general_search
from langgraph.checkpoint.memory import InMemorySaver
from typing import Literal

def route_after_chatbot(state: AgentState) -> Literal["orchestrator", "__end__"]:
    """Route from chatbot to orchestrator or end"""
    if state.get("route_to_orch"):
        return "orchestrator"
    else:
        return "__end__"

def route_after_orchestrator(state: AgentState) -> Literal["tools", "planner", "__end__"]:
    """Route based on orchestrator's decision"""
    next_action = state.get("next_action")
    
    if next_action == "tools":
        return "tools"
    elif next_action == "planner":
        return "planner"
    elif next_action == "end":
        return "__end__"
    else:
        # Default fallback
        if state.get("pending_tasks"):
            return "tools"
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