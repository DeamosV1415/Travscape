from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from agents.routing_schemas import (
    TravscapeState,
    ChatbotOutput,
    PlannerOutput,
    OrchestratorOutput,
)
from agents.prompts import chatbot_message, planner_message, orchestrator_message
from agents.utils import get_today_str, flight_search_tool, maps_text_search, general_search


# ==================== NODE IMPLEMENTATIONS ====================

async def chatbot_node(state: TravscapeState) -> TravscapeState:
    """
    Chatbot node - handles initial user interaction and trip extraction.
    
    Returns to user if clarification needed, otherwise routes to orchestrator.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
    structured_llm = llm.with_structured_output(ChatbotOutput)
    
    # Get latest user message
    user_msg = state["messages"][-1].content if state["messages"] else ""
    
    # Build prompt with context
    prompt = chatbot_message.format(date=get_today_str())
    
    # Invoke chatbot
    response: ChatbotOutput = await structured_llm.ainvoke([
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_msg}
    ])
    
    # Update state
    return {
        **state,
        "user_request": [req.model_dump() for req in response.user_request],
        "needs_user_clarification": response.need_clarification,
        "clarification_question": response.clarification_question,
        "messages": state["messages"] + [AIMessage(content=response.chatbot_reply)],
        "next_action": "end" if response.need_clarification else "orchestrator"
    }


async def planner_node(state: TravscapeState) -> TravscapeState:
    """
    Planner node - creates strategic travel plan with search tasks.
    
    Can ask for clarification or return plan with search tasks.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
    structured_llm = llm.with_structured_output(PlannerOutput)
    
    # Prepare trip details from user_request
    trip_details = state["user_request"][0] if state["user_request"] else {}
    
    # Build prompt
    prompt = planner_message.format(
        date=get_today_str(),
        trip_details=trip_details
    )
    
    # Invoke planner
    response: PlannerOutput = await structured_llm.ainvoke([
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Create the travel plan based on the trip details."}
    ])
    
    # If planner needs clarification, route back to chatbot
    if response.need_clarification:
        return {
            **state,
            "needs_user_clarification": True,
            "clarification_question": response.clarification_question,
            "next_action": "chatbot"
        }
    
    # Extract search tasks from plan
    plan_dict = response.plan.model_dump() if response.plan else {}
    search_tasks = plan_dict.get("search_tasks", [])
    pending_task_ids = [task["task_id"] for task in search_tasks]
    
    return {
        **state,
        "trip_plan": plan_dict,
        "pending_tasks": pending_task_ids,
        "completed_tasks": [],
        "search_results": {},
        "conversation_state": "searching",
        "next_action": "orchestrator"
    }


async def orchestrator_node(state: TravscapeState) -> TravscapeState:
    """
    Orchestrator node - ReAct agent that coordinates the workflow.
    
    Decides to:
    - Call tools for search tasks
    - Route to planner for new trip requests
    - Route to chatbot for clarification
    - Complete when all tasks done
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
    
    # Bind tools to LLM so it can generate tool calls
    tools = [flight_search_tool, maps_text_search, general_search]
    llm_with_tools = llm.bind_tools(tools)
    
    # Build context for orchestrator
    prompt = orchestrator_message.format(
        date=get_today_str(),
        conversation_state=state.get("conversation_state", "greeting"),
        user_message=state["messages"][-1].content if state["messages"] else "",
        chat_history=state.get("messages", []),
        trip_plan=state.get("trip_plan", {}),
        search_results=state.get("search_results", {}),
        pending_tasks=state.get("pending_tasks", []),
        completed_tasks=state.get("completed_tasks", []),
        iteration=state.get("iteration", 0),
        max_iterations=state.get("max_iterations", 10)
    )
    
    # Invoke orchestrator with tools
    response = await llm_with_tools.ainvoke([
        {"role": "system", "content": prompt}
    ])
    
    # Update iteration counter
    new_iteration = state.get("iteration", 0) + 1
    
    # Check if LLM generated tool calls
    if response.tool_calls:
        # LLM decided to call tools - route to ToolNode
        return {
            **state,
            "iteration": new_iteration,
            "next_action": "tools",
            "messages": state["messages"] + [response]
        }
    
    # Otherwise, parse structured output for routing decision
    structured_llm = llm.with_structured_output(OrchestratorOutput)
    decision: OrchestratorOutput = await structured_llm.ainvoke([
        {"role": "system", "content": prompt}
    ])
    
    # Route based on decision
    if decision.action == "ROUTE_TO_PLANNER":
        return {
            **state,
            "iteration": new_iteration,
            "next_action": "planner",
            "messages": state["messages"] + [AIMessage(content=decision.status_message)]
        }
    
    elif decision.action == "ROUTE_TO_CHATBOT":
        return {
            **state,
            "iteration": new_iteration,
            "needs_user_clarification": True,
            "clarification_question": decision.clarification_message,
            "next_action": "chatbot",
            "messages": state["messages"] + [AIMessage(content=decision.clarification_message)]
        }
    
    elif decision.action == "COMPLETE":
        return {
            **state,
            "iteration": new_iteration,
            "conversation_state": "complete",
            "next_action": "end",
            "messages": state["messages"] + [AIMessage(content=decision.final_response)]
        }
    
    else:
        # Default: end
        return {
            **state,
            "iteration": new_iteration,
            "next_action": "end"
        }


# ==================== ROUTING FUNCTIONS ====================

def route_after_chatbot(state: TravscapeState) -> Literal["orchestrator", "__end__"]:
    """Route from chatbot to orchestrator or end"""
    if state["needs_user_clarification"]:
        return "__end__"  # Wait for user response
    elif state.get("user_request"):
        return "orchestrator"  # Has trip request, proceed to orchestrator
    else:
        return "__end__"  # Casual conversation, done


def route_after_orchestrator(state: TravscapeState) -> Literal["tools", "planner", "chatbot", "__end__"]:
    """Route based on orchestrator's decision"""
    next_action = state.get("next_action")
    
    if next_action == "tools":
        return "tools"
    elif next_action == "planner":
        return "planner"
    elif next_action == "chatbot":
        return "chatbot"
    else:
        return "__end__"


def route_after_planner(state: TravscapeState) -> Literal["chatbot", "orchestrator"]:
    """Route from planner back to orchestrator or chatbot"""
    if state["needs_user_clarification"]:
        return "chatbot"
    else:
        return "orchestrator"


def route_after_tools(state: TravscapeState) -> Literal["orchestrator"]:
    """After tools execute, always return to orchestrator to process results"""
    return "orchestrator"


# ==================== GRAPH CONSTRUCTION ====================

def create_orchestrator_graph():
    """
    Build and compile the complete orchestrator graph.
    
    Returns:
        Compiled LangGraph application with checkpointing
    """
    # Initialize graph with state schema
    workflow = StateGraph(TravscapeState)
    
    # Create tool node with all available tools
    tools = [flight_search_tool, maps_text_search, general_search]
    tool_node = ToolNode(tools)
    
    # Add all nodes
    workflow.add_node("chatbot", chatbot_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("tools", tool_node)
    
    # Set entry point - all conversations start with chatbot
    workflow.set_entry_point("chatbot")
    
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
            "chatbot": "chatbot",
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
    
    # Compile with memory checkpointing for persistence
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    return graph


# ==================== USAGE EXAMPLE ====================

async def run_orchestrator(user_message: str, thread_id: str = "default"):
    """
    Run the orchestrator graph with a user message.
    
    Args:
        user_message: The user's input message
        thread_id: Conversation thread ID for checkpointing
        
    Returns:
        Final state after graph execution
    """
    graph = create_orchestrator_graph()
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "user_request": None,
        "trip_plan": None,
        "pending_tasks": [],
        "completed_tasks": [],
        "search_results": {},
        "conversation_state": "greeting",
        "needs_user_clarification": False,
        "clarification_question": None,
        "iteration": 0,
        "max_iterations": 10,
        "next_action": None
    }
    
    # Run graph
    config = {"configurable": {"thread_id": thread_id}}
    final_state = await graph.ainvoke(initial_state, config)
    
    return final_state


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        result = await run_orchestrator("Plan a 3-day trip to Paris")
        print("Final response:", result["messages"][-1].content)
    
    asyncio.run(main())
