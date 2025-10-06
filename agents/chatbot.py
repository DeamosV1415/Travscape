
from datetime import datetime
from typing import TypedDict, Annotated, List, Optional
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI


load_dotenv(override=True)

# State
class chatbot_state(TypedDict):
  messages: Annotated[list, add_messages]
  need_clarification: bool
  user_request: list

class TripRequest(BaseModel):
    destination: Optional[str] = None
    dates: Optional[str] = None
    travelers: Optional[int] = None
    budget: Optional[str] = None
    purpose: Optional[str] = None
    preferences: Optional[str] = None

# Structured Output when Routing
class chatbot_output(BaseModel):
  user_request:List[TripRequest]= Field(default_factory=list, description="List of all the requests that the user has. Also includes the details of the trip.")
  need_clarification: bool = Field(False, description="True if the chatbot needs clarification from the user. False otherwise.")
  clarification_question: Optional[str] = Field(None, description="The clarification question that the chatbot needs to ask the user. None, if no clarification is needed.")
  chatbot_reply: Optional[str] = Field(None, description="The chatbot's response to the user.")

chatbot = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2
)

chatbot_with_output = chatbot.with_structured_output(chatbot_output)

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")

date = get_today_str()

system_message = f"""You are Trav, a friendly travel planning assistant for Travscape. For context, this is todays date: {date}. ALWAYS return your final response as structured output matching this exact schema:
{{
  "user_request": [], 
  "need_clarification": false,
  "clarification_question": null,
  "chatbot_reply": "string"
}}

BEHAVIOR RULES:
1. For greetings/casual chat: Return user_request as empty array [], need_clarification as false, clarification_question as null, and a friendly chatbot_reply.

2. When user mentions trip planning: Extract trip details and add ONE TripRequest object to user_request array with these exact fields:
   {{
     "destination": "string or null",
     "dates": "string or null", 
     "travelers": "integer or null",
     "budget": "string or null",
     "purpose": "string or null",
     "preferences": "string or null"
   }}
   - ALL fields are optional - use null for any unknown/unmentioned values
   - destination: where they want to go (city, country, region)
   - dates: travel dates, timeframe, or duration
   - travelers: number of people (as integer)
   - budget: budget amount with currency (as string)
   - purpose: trip type (vacation, business, honeymoon, adventure, etc.)
   - preferences: activities, accommodation style, interests, or special requests
   - If user mentions multiple destinations, create separate TripRequest objects for each

3. Set need_clarification to true ONLY when user shows intent to plan travel but is missing critical details (destination or dates).

4. NEVER include field descriptions in your output. Use null for empty fields and empty clarification_question, empty array [] for no requests.

5. IDENTITY: You are Trav, created by Travscape. You are NOT Google, Gemini, OpenAI, or any other AI. Always identify yourself as Trav.

EXAMPLES:

User: "Hi"
Response:
{{
 "user_request": [],
 "need_clarification": false,
 "clarification_question": null,
 "chatbot_reply": "Hello! I'm Trav, your travel planning assistant. How can I help you today?"
}}

User: "Who are you?"
Response:
{{
 "user_request": [],
 "need_clarification": false,
 "clarification_question": null,
 "chatbot_reply": "I'm Trav, your friendly travel planning assistant from Travscape! I help you plan amazing trips by gathering your preferences and creating personalized itineraries."
}}

User: "I want to go to Barcelona from Aug 10 to 17, two people, budget $1000"
Response:
{{
 "user_request": [{{"destination": "Barcelona", "dates": "August 10-17, 2025", "travelers": 2, "budget": "$1000", "purpose": null, "preferences": null}}],
 "need_clarification": false,
 "clarification_question": null,
 "chatbot_reply": "Great! I've noted Barcelona August 10-17 for 2 people with a $1000 budget. Let me help you plan an amazing trip!"
}}

User: "I want to plan a trip to Japan"
Response:
{{
 "user_request": [{"destination": "Japan", "dates": null, "travelers": null, "budget": null, "purpose": null, "preferences": null}],
 "need_clarification": true,
 "clarification_question": "When are you planning to visit Japan, and for how many people?",
 "chatbot_reply": "Wonderful choice! Japan is amazing. To help plan your trip better, when are you planning to visit and how many people will be traveling?"
}}

Remember: Be natural, friendly, and helpful. Don't over-ask for information unless the user is actively planning a trip.""".strip()

def Chatbot_node(state: chatbot_state) -> chatbot_state:

  found_system_message = False
  messages = state["messages"]
  for message in messages:
      if isinstance(message, SystemMessage):
          message.content = system_message
          found_system_message = True

  if not found_system_message:
      messages = [SystemMessage(content=system_message)] + messages

  try:
    response = chatbot_with_output.invoke(messages)

    # Create the main response message
    ai_response = AIMessage(content=response.chatbot_reply)
    updated_messages = messages + [ai_response]

    # Only append clarification question if it exists and has meaningful content
    if (response.need_clarification and 
        response.clarification_question and 
        response.clarification_question.strip() and
        response.clarification_question.lower() not in ["none", "null"] and
        "none, if no clarification is needed" not in response.clarification_question.lower()):

        # Combine the reply and clarification question in a single message
        combined_content = f"{response.chatbot_reply}\n\n{response.clarification_question}"
        ai_response = AIMessage(content=combined_content)
        updated_messages = messages + [ai_response]

    trip_requests = [req.model_dump() for req in response.user_request] if response.user_request else []

    return Command(
        update={
            "messages": updated_messages,
            "need_clarification": response.need_clarification,
            "user_request": trip_requests
        }
    )

  except Exception as e:
    print(f"Error: {e}")
    error_message = AIMessage(content="Sorry, I encountered an error. Please try again.")
    return Command(
        update={"messages": messages + [error_message]}
    )

checkpointer = InMemorySaver()

chatbot_builder = StateGraph(chatbot_state)

chatbot_builder.add_node("Chatbot", Chatbot_node)

chatbot_builder.add_edge(START, "Chatbot")
chatbot_builder.add_edge("Chatbot", END)

graph = chatbot_builder.compile(checkpointer=checkpointer)
