from langgraph.graph import  StateGraph,START,END
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_groq import ChatGroq
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage,BaseMessage,SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from time import sleep
import requests




# ------------------------------others--------------------------
from dotenv import load_dotenv
import os
from typing import TypedDict,List,Annotated,Literal
load_dotenv()


weather_api_key = os.getenv("WEATHER_API")

llm = ChatGroq(model="llama-3.3-70b-versatile",temperature=0.8)

os.environ['LANGCHAIN_PROJECT'] = "TOOls_graph"

# ------------------------------------------------------------------



# state
class ChatState(TypedDict):
    messages:Annotated[List[BaseMessage],add_messages]






# tools

@tool
def weather(state_name:str,country_name:str,aqi:Literal["yes","no"]):
    """
    Get current weather related data for a given state and country.
    Optionally include air quality index (aqi).
    """
    request_url = weather_api_key + f"q={state_name},{country_name}&aqi={aqi}"
    res = requests.get(url=request_url)
    sleep(0.4)
    return res.json()





@tool
def calculator(first_num: float, second_num: float, operation: str) -> str:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div.
    Use ONLY for math calculations. Do NOT guess numbers.
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return "Error: Division by zero is not allowed"
            result = first_num / second_num
        else:
            return f"Error: Unsupported operation '{operation}'"

        return f"Result of {operation} between {first_num} and {second_num} is {result}"

    except Exception as e:
        return f"Error: {str(e)}"


tools = [calculator,weather]

llm_with_tools = llm.bind_tools(tools=tools)


#nodes
def llm_with_tool_node(state:ChatState):
    messages = state["messages"]
    prompt = [SystemMessage(content="""
                        You are a helpful AI assistant.
                        Rules:
                        - Use tools ONLY when necessary.
                        - do not use Tools when queries are already solved.
                        - call tools only when needed.
                        - Do NOT manually write tool calls.
                        - never return raw data from tools try to beautify those.
                        """)]
    response = llm_with_tools.invoke(prompt + messages)
    return {"messages":[response]}
def tool_output_refine(state:ChatState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages":[response]}

tool_node = ToolNode(tools)

graph = StateGraph(ChatState)
# add nodes in graph
graph.add_node("chat_node",llm_with_tool_node)
graph.add_node("tools",tool_node)
# graph.add_node("tools_output_refine",tool_output_refine)


# add Edges
graph.add_edge(START,"chat_node")
graph.add_conditional_edges(
    "chat_node",
    tools_condition
)
graph.add_edge("tools","chat_node")





conn = sqlite3.connect(database="chatbot.db",check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)

chatbot_with_tools=graph.compile(checkpointer=checkpointer)

# config = {"configurable":{"thread_id":"15672"}}

# while True:
#     user_input =str(input("Enter Chat:  "))
#     try :
#         out = chatbot_with_tools.invoke({"messages":[HumanMessage(content=user_input)]},config=config)
#         print("\nAI: ",out['messages'][-1].content)
#     except Exception as e:
#         print(e)
#     if any( word in user_input.strip() for word in ['bye','exit','quit']):
#         break
#     print("\n")