from agents.GlobalState import AgentState
from agents.orchestrator_output import OrchestratorOutput
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agents.prompts import orchestrator_message
from agents.utils import get_today_str, flight_search_tool, maps_text_search, general_search
from langchain_core.command import Command

tool_map = {
    "Flight Search": flight_search_tool,
    "Maps Text Search": maps_text_search,
    "General Search": general_search,
}

async def orchestrator_node(state: AgentState) -> AgentState:

  llm = ChatOpenAI(model="gpt-4o-mini")
  structured_llm = llm.with_structured_output(OrchestratorOutput)

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

  found_system_message = False
  messages = state["messages"]
  for message in messages:
      if isinstance(message, SystemMessage):
          message.content = system_message
          found_system_message = True

  if not found_system_message:
      messages = [SystemMessage(content=system_message)] + messages

  try:
    orchestrator_response = await structured_llm.ainvoke(messages)

    ai_response = [AIMessage(content=orchestrator_response.thought)] + [AIMessage(content=orchestrator_response.status_message)]
    updated_messages = messages + ai_response

    return Command(
      update={
        "messages": updated_messages,
        "orchestrator_output": orchestrator_response,
        "next_action": orchestrator_response.action,
        "pending_tasks": orchestrator_response.pending_tasks,
        "completed_tasks": orchestrator_response.completed_tasks,
      }
    )

  except Exception as e:
    print(f"Error: {e}")
    error_message = AIMessage(content="Sorry, I encountered an error. Please try again.")
    return Command(
      update={"messages": messages + [error_message]}
    )

async def tool_dispatcher_node(state: AgentState) -> Command:
    """
    Executes the tool calls requested by the orchestrator and returns the results.
    This node only runs if the orchestrator's action is 'CALL_TOOL'.
    """
    # Get the orchestrator's decision from the state
    orchestrator_decision = state['orchestrator_output']
    tool_calls = orchestrator_decision.tool_calls
    
    if not tool_calls:
        return Command(
      update={
        "tool_results": []
      }
    )

    tool_results = []
    for tool_call in tool_calls:
        tool_name = tool_call.tool_name
        tool_input = tool_call.tool_input
        
        # Look up the function in our map
        tool_function = tool_map.get(tool_name)
        
        if not tool_function:
            # Handle the case where the LLM hallucinates a tool name
            result = f"Error: Tool '{tool_name}' not found."
        else:
            try:
                # Execute the tool by unpacking the input dictionary as keyword arguments
                result = await tool_function(**tool_input)
            except Exception as e:
                # Robustly handle any errors during tool execution
                result = f"Error executing tool '{tool_name}': {e}"

        tool_results.append({
            "tool_name": tool_name,
            "tool_output": result
        })
        
    new_iteration = state.get("iteration", 0) + 1
    
    # Return the results to be added to the state
    return Command(
      update={
        "tool_results": tool_results,
        "iteration": new_iteration
      }
    )

def after_orchestrator_router(state: AgentState) -> str:
    """
    Inspects the orchestrator's decision and routes to the next appropriate node.
    """
    action = state['next_action']

    if action == "CALL_TOOL" and state['iteration'] < state['max_iterations']:
        return "tool_dispatcher"
    elif action == "ROUTE_TO_PLANNER":
        return "planner_node"
    elif action == "ROUTE_TO_CHATBOT":
        return "chatbot_node"
    elif action == "COMPLETE":
        return END
    else:
        return END
