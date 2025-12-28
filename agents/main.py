import sys
from pathlib import Path

# Add parent directory to Python path to ensure imports work
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from agents.routing_and_graph import create_graph
from langchain_core.messages import HumanMessage

# async def run_orchestrator(user_message: str, thread_id: str = "default"):
#     """
#     Run the orchestrator graph with a user message.
    
#     Args:
#         user_message: The user's input message
#         thread_id: Conversation thread ID for checkpointing
        
#     Returns:
#         Final state after graph execution
#     """
#     graph = create_graph()
    
#     # Initial state
#     initial_state = {
#         "messages": [HumanMessage(content=user_message)],
#         "user_request": [],
#         "need_trip_plan": False,
#         "needs_clarification": False,
#         "trip_plan": {},
#         "orchestrator_output": {},
#         "next_action": "",
#         "tool_results": [],
#         "pending_tasks": [],
#         "completed_tasks": [],
#         "iteration": 0,
#         "max_iterations": 10
#     }
    
#     # Run graph
#     config = {"configurable": {"thread_id": thread_id}}
#     final_state = await graph.ainvoke(initial_state, config)
    
#     return final_state
import gradio as gr

# Create graph ONCE at module level so memory persists across messages
graph = create_graph()
config = {"configurable": {"thread_id": "1"}}

async def chat(message, history):
    try:
        # Extract user message content
        user_message = message if isinstance(message, str) else message.get("text", "")
        
        # Only pass the new message - the graph will load previous state from checkpointer
        # Invoke the graph
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=user_message)]}, 
            config=config
        )
        
        # Return the assistant's response in proper format
        assistant_response = result["messages"][-1].content
        return assistant_response
        
    except Exception as e:
        print(f"Chat error: {e}")
        return (f"Sorry, I encountered an error. -> {e}")

if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        title="Trav - Your Travel Planning Assistant",
        description="Hi! I'm Trav, ready to help you plan your next adventure!"
    ).launch()
