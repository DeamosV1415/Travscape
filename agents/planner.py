from agents.utils import get_today_str
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from agents.GlobalState import AgentState
from agents.planner_output import PlannerOutput
from agents.prompts import planner_message
from agents.utils import get_today_str

load_dotenv(override=True)

################Example:
'''trip_details = {
      "destination": "Tokyo",
      "dates": "October 10, 2025",
      "no._of_days": 5,
      "travelers": 3,
      "budget": "Budget trip",
      "purpose": "sightseeing",
      "preferences": None
    }'''
################

planner = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2
)

planner_with_output = planner.with_structured_output(PlannerOutput)

#System message initialization with today's date
system_message = planner_message.format(
  date=get_today_str(),
  trip_details=trip_details
)

def Planner_node(state:AgentState) -> AgentState:

    found_system_message = False
    messages = state["messages"]
    for message in messages:
        if isinstance(message, SystemMessage):
            message.content = system_message
            found_system_message = True

    if not found_system_message:
        messages = [SystemMessage(content=system_message)] + messages

    try:
        response = planner_with_output.invoke(messages)

        if response.need_clarification and response.clarification_question is not None:
          ai_response = AIMessage(content=response.clarification_question)
          updated_messages = messages + [ai_response]

          return Command(
              update={
                  "messages": updated_messages
              }
          )

        else:
            plan_dict = response.plan.model_dump() if response.plan else {}
            ai_response = AIMessage(content=f"Plan generated: {plan_dict}")
            updated_messages = messages + [ai_response]

            return Command(
                update={
                    "messages": updated_messages,
                    "trip_plan": [plan_dict]
                }
            )

    except Exception as e:
        print(f"Error: {e}")
        error_message = AIMessage(content="Sorry, I encountered an error. Please try again.")
        return Command(
            update={"messages": messages + [error_message]}
        )

checkpointer = InMemorySaver()

planner_builder = StateGraph(AgentState)

planner_builder.add_node("Planner", Planner_node)

planner_builder.add_edge(START, "Planner")
planner_builder.add_edge("Planner", END)

graph = planner_builder.compile(checkpointer=checkpointer)

