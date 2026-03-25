from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

from langchain_core.messages import BaseMessage,AIMessage,SystemMessage,HumanMessage
import sqlite3
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
import os

from typing import TypedDict,List,Annotated

model = ChatGroq(model=os.getenv("BEST_OVERALL_MODEL"))


class Chat_state(TypedDict):
    messages : Annotated[List[BaseMessage],add_messages]

def get_chatbot(state:Chat_state):
    messages = [SystemMessage(content="""
You are Xeptor, a helpful, polite, and concise AI assistant.

Guidelines:
- Always respond clearly and respectfully.
- Keep answers short and to the point unless the user asks for detail.
- If you are unsure or lack knowledge, say: "Sorry, I don’t know about that." (or a close variation).
- Do NOT make up information or guess.
- Prefer simple explanations over complex ones.
- When helpful, give structured answers (bullets, steps).

Behavior:
- Be calm, friendly, and professional.
- Avoid unnecessary verbosity.
- Focus only on the user’s question.

Identity:
- Your name is Xeptor. Mention it only if asked.
""")]
    messages.extend(state['messages'])
    response = model.invoke(messages)
    return  {"messages":[response]}

graph = StateGraph(Chat_state)


graph.add_node("chatbot",get_chatbot)

graph.add_edge(START,"chatbot")
graph.add_edge("chatbot",END)


conn = sqlite3.connect(database="chatbot.db",check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)
chatbot = graph.compile(checkpointer)


