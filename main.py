# travel_assistant.py
from agents.routing_and_graph import create_graph
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import asyncio

class TravelAssistant:
    """
    Production-ready travel assistant with multi-user support.
    """
    
    def __init__(self):
        """Initialize the assistant with a graph and message tracking."""
        print("Initializing TravelAssistant...")
        self.graph = create_graph()
        print("TravelAssistant initialized successfully!")
    
    async def chat(self, message: str, thread_id: str):
        """
        Stream only the NEWEST AI message content.
        Handles cases where the graph might return the full history.
        """
        try:
            config = {"configurable": {"thread_id": thread_id}}
            user_message = HumanMessage(content=message)
            
            # 1. Get the current state to identify existing AI messages
            current_state = await self.graph.aget_state(config)
            existing_messages = current_state.values.get("messages", [])
            
            # Get the last AI message content if it exists
            last_ai_content = ""
            for msg in reversed(existing_messages):
                if isinstance(msg, AIMessage):
                    last_ai_content = msg.content
                    break
            
            streamed_anything = False
            full_response_received = ""
            
            # ⭐ Use astream_events for more granular control if needed, 
            # but sticking to 'updates' and fixing the logic.
            async for event in self.graph.astream(
                {"messages": [user_message]},
                config=config,
                stream_mode="updates"
            ):
                for node_name, state_update in event.items():
                    messages = state_update.get("messages", [])
                    if not messages:
                        continue
                    
                    # In LangGraph, the last message in the update is usually the most recent one
                    new_msg = messages[-1]
                    
                    if isinstance(new_msg, AIMessage) and new_msg.content:
                        new_content = new_msg.content
                        
                        # If this message is exactly the same as the last one we saw in history, skip it
                        if new_content == last_ai_content:
                            continue
                            
                        # If the new content starts with the old content, it's a "growing" message
                        # We only want the part that was added.
                        delta = new_content
                        if last_ai_content and new_content.startswith(last_ai_content):
                            delta = new_content[len(last_ai_content):].strip()
                        
                        # If we've already streamed something in this turn, we only stream the delta 
                        # relative to what we've already sent in this turn.
                        if streamed_anything:
                            if new_content.startswith(full_response_received):
                                delta = new_content[len(full_response_received):]
                            else:
                                # This is a completely different message from a different node
                                delta = "\n" + new_content
                        
                        if not delta:
                            continue
                            
                        # Update our tracking
                        full_response_received = new_content
                        streamed_anything = True
                        
                        # Stream the delta with typewriter effect
                        chunk_size = 5
                        for i in range(0, len(delta), chunk_size):
                            chunk_text = delta[i:i + chunk_size]
                            yield chunk_text
                            await asyncio.sleep(0.01)
            
        except Exception as e:
            print(f"Chat error: {e}")
            yield f"\n\nError: {e}"
