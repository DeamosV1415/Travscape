# travel_assistant.py
from agents.routing_and_graph import create_graph
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import asyncio
import json


def _strip_json_state(text: str) -> str:
    """Remove leaked JSON state blocks from response text.
    These blocks come from structured output schemas leaking into the chat."""
    STATE_KEYS = ('"user_request"', '"chatbot_reply"', '"need_clarification"', '"needs_clarification"')
    result = []
    i = 0
    while i < len(text):
        if text[i] == '{':
            # Find matching closing brace
            depth = 1
            j = i + 1
            while j < len(text) and depth > 0:
                if text[j] == '{': depth += 1
                elif text[j] == '}': depth -= 1
                j += 1
            block = text[i:j]
            if any(k in block for k in STATE_KEYS):
                i = j
                # Skip trailing whitespace
                while i < len(text) and text[i] in '\n\r ':
                    i += 1
                continue
            else:
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result).strip()

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
        Stream only the FINAL AI message content from the graph execution.
        Filters out intermediate node messages (planner routing, orchestrator reasoning).
        """
        # Known intermediate messages that should never be shown to the user
        SKIP_PATTERNS = (
            "Let me create a detailed trip plan",
            "Plan generated",
            "I need some clarification",
            "I'm not sure what to do next",
        )

        try:
            config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 15}
            user_message = HumanMessage(content=message)
            
            # Collect all node outputs, we'll only stream the last meaningful one
            collected_responses = []
            
            async for event in self.graph.astream(
                {"messages": [user_message]},
                config=config,
                stream_mode="updates"
            ):
                for node_name, state_update in event.items():
                    messages = state_update.get("messages", [])
                    if not messages:
                        continue
                    
                    new_msg = messages[-1]
                    
                    if isinstance(new_msg, AIMessage) and new_msg.content:
                        content = _strip_json_state(new_msg.content)
                        
                        if not content:
                            continue
                        
                        # Skip known intermediate messages
                        if any(content.strip().startswith(pat) for pat in SKIP_PATTERNS):
                            continue
                        
                        # Skip tool-calling messages (they have tool_calls but may also have content)
                        if hasattr(new_msg, "tool_calls") and new_msg.tool_calls:
                            continue
                        
                        collected_responses.append((node_name, content))
            
            # Stream the LAST meaningful response (which is typically the final answer)
            # But if chatbot was the only node (greeting/clarification), use that
            if not collected_responses:
                return
            
            # Use the last collected response
            final_content = collected_responses[-1][1]
            
            # Stream with typewriter effect
            chunk_size = 5
            for i in range(0, len(final_content), chunk_size):
                chunk_text = final_content[i:i + chunk_size]
                yield chunk_text
                await asyncio.sleep(0.01)
            
        except Exception as e:
            print(f"Chat error: {e}")
            yield f"\n\nError: {e}"

