from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode,tools_condition,InjectedState

from langchain_core.messages import BaseMessage,AIMessage,SystemMessage,HumanMessage
import sqlite3
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
import os
from typing import TypedDict,List,Annotated,Literal,Dict,Any
from pydantic import Field


from RAG.retrievers import FaissRetriever,get_retrieverContent
from RAG.prompts import RetrieverPrompt





os.environ["LANGCHAIN_TRACING_V2"] = "true"
model = ChatGroq(model=os.getenv("BEST_OVERALL_MODEL"))



class RAGState (TypedDict):
    doctype:Literal['pdf',"txt","url"]
    path:Annotated[str,Field(description="if doctype is in [pdf,txt] then path would be tempfile-path and if doctype is url then path is url")]
    topk:Annotated[int,Field(description="top k result will be shown by the retriever")]=5
    loop_cycle:int=0


class Chat_state(TypedDict):
    messages : Annotated[List[BaseMessage],add_messages]
    rags_info: RAGState
    active_rag:Dict[str,Any]












def Chat_condition(state: Chat_state):
    msg = state["messages"][-1]
    prompt ="""
    You are a query classifier. Analyze the user message and classify it into exactly one of these categories:

                    1. **normal_chat** - General conversation, greetings, opinions, casual questions, or anything that can be answered from general knowledge (e.g., "What is Python?", "How are you?", "Tell me a joke")

                    2. **rag_based_chat** - Questions that require retrieving specific information from a document, database, or knowledge base (e.g., "What does the contract say about X?", "Summarize the uploaded report", "Find details about [specific topic] in the document")

                    User Message: {msg}

                    Rules:
                    - Return ONLY the category name: normal_chat or rag_based_chat
                    - No explanation, no punctuation, just the label
                    - When in doubt, prefer normal_chat

                    Classification:
                """
    response = model.invoke(prompt)
    cat = response.content
    if cat.lower() == "rag_based_chat".lower():
        return "rag_based_chat"
    else :
        return "normal_chat"


def get_chatbot(state:Chat_state):
    messages = [SystemMessage(content="""
You are VighnaMitra Ai, a helpful, polite, and concise AI assistant.

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


def is_rag_exist_condition(state: Chat_state) -> str:
    path = state['rags_info']['path']
    if path not in state['active_rag']:
        return "load_rag"   # Route to node that loads the retriever
    return "query_rag"



def load_rag(state: Chat_state):
    rag_info = state.get("rags_info", {})
    path = rag_info.get("path")
    doctype = rag_info.get("doctype")
    topk = rag_info.get("topk")
    
    existing_rags = state.get("active_rag", {})
    
    # Increment loop cycle
    new_loop_cycle = rag_info.get("loop_cycle", 0) + 1
    
    return {
        "active_rag": {
            **existing_rags,
            path: FaissRetriever(doctype=doctype, topk=topk, file_path=path)
        },
        "rags_info": {**rag_info, "loop_cycle": new_loop_cycle}  # Update it
    }

def query_rag(state: Chat_state):
    query= state["messages"][-1].content
    path = state['rags_info']['path']
    try:
        retriever = state["active_rag"][path]
        retrieved_docs = retriever.invoke(query)
        retrieved_context = "\n".join([doc.page_content for doc in retrieved_docs])
        chain = RetrieverPrompt | model
        response = chain.invoke({"context":retrieved_context,"userquery":query})

        return {"messages":[response]}


    except Exception as e:
        raise e

def check_rag_info(state: Chat_state):
    path = state['rags_info']['path']
    doctype = state['rags_info']['doctype']

    loop_cycle = state['rags_info']['loop_cycle']

    if loop_cycle >3:
        raise RuntimeError("loop is going too far!.")




    if not any([path,doctype]):
        raise ValueError("no document/Urls is Uploaded!")



    return state



graph = StateGraph(Chat_state)


graph.add_node("check_rag_info",check_rag_info)

#chat condition:


# if normal
graph.add_node("chatbot",get_chatbot)
#if rag
graph.add_node("load_rag",load_rag)
graph.add_node("query_rag",query_rag)

graph.add_conditional_edges(START,Chat_condition,{
    "normal_chat":"chatbot",
    "rag_based_chat":"check_rag_info"
    })

graph.add_conditional_edges("check_rag_info",is_rag_exist_condition,{
    "load_rag":"load_rag",
    "query_rag":"query_rag"
})


graph.add_edge("load_rag","check_rag_info")
graph.add_edge("query_rag",END)
graph.add_edge("chatbot",END)


conn = sqlite3.connect(database="chatbot.db",check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)
chatbot_with_rag = graph.compile(checkpointer)


