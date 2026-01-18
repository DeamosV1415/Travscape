from agents.utils import get_today_str
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from agents.GlobalState import AgentState
from agents.chatbot_output import chatbot_output
from agents.prompts import chatbot_message

load_dotenv(override=True)

async def chatbot_node(state: AgentState) -> AgentState:

    chatbot = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    chatbot_with_output = chatbot.with_structured_output(chatbot_output, method="function_calling")

    #System message initialization with today's date
    system_message = chatbot_message.format(
        date=get_today_str()
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
        response = await chatbot_with_output.ainvoke(messages)

        # Create the main response message
        ai_response = AIMessage(content=response.chatbot_reply)
        updated_messages = messages + [ai_response]

        # Only append clarification question if it exists and has meaningful content
        if (response.needs_clarification and 
            response.clarification_question and 
            response.clarification_question.strip() and
            response.clarification_question.lower() not in ["none", "null"] and
            "none, if no clarification is needed" not in response.clarification_question.lower()):

            # Combine the reply and clarification question in a single message
            combined_content = f"{response.chatbot_reply}\n\n{response.clarification_question}"
            ai_response = AIMessage(content=combined_content)
            updated_messages = messages + [ai_response]

        trip_requests = [req.model_dump() for req in response.user_request] if response.user_request else []

        # Ensure need_trip_plan is explicitly set based on the response
        need_trip_plan = response.need_trip_plan
        
        # If it's a simple search request, ensure need_trip_plan is False
        # This is a safety check in case the LLM misses the prompt instruction
        if any(req.get("purpose") and "search" in req.get("purpose").lower() for req in trip_requests):
            need_trip_plan = False

        return Command(
            update={
                "messages": updated_messages,
                "needs_clarification": response.needs_clarification,
                "user_request": trip_requests,
                "need_trip_plan": need_trip_plan,
                "route_to_orch": response.route_to_orch
            }
        )

    except Exception as e:
        print(f"Error: {e}")
        error_message = AIMessage(content="Sorry, I encountered an error. Please try again.")
        return Command(
            update={"messages": messages + [error_message]}
        )

# checkpointer = InMemorySaver()

# chatbot_builder = StateGraph(AgentState)

# chatbot_builder.add_node("Chatbot", chatbot_node)

# chatbot_builder.add_edge(START, "Chatbot")
# chatbot_builder.add_edge("Chatbot", END)

# graph = chatbot_builder.compile(checkpointer=checkpointer)
