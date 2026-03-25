import streamlit as st
from langchain_core.messages import BaseMessage,HumanMessage
from backend.chatbot import chatbot
from uuid import uuid4
import sqlite3


#------------ Session Id / conversation id -------------------

if "thread_id" not in st.session_state:
    st.session_state['thread_id'] = str(uuid4())

thread_id = st.session_state['thread_id']

import sqlite3
import os

def get_all_threads(db_path="chatbot.db"):
    # Step 1: ensure DB file exists
    if not os.path.exists(db_path):
        # create empty DB file
        conn = sqlite3.connect(db_path)
        conn.close()
        return []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 2: check if checkpoints table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='checkpoints'
    """)
    
    table_exists = cursor.fetchone()

    if not table_exists:
        conn.close()
        return []

    # Step 3: fetch thread_ids
    cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]







def get_messages(thread_id):
    state = chatbot.get_state(config={"configurable":{"thread_id":thread_id}})
    return state.values.get("messages",[])


st.sidebar.header("LangGraph chatbot")
# new chat
if st.sidebar.button("new chat"):
    new_id = str(uuid4())
    st.session_state['thread_id'] = new_id

    st.rerun()


keys = get_all_threads()



st.sidebar.header("Chat history")


if not keys:
    st.sidebar.write("No chats yet")
for idx in range(len(keys)):
    hist_id = keys[idx]
    if st.sidebar.button(hist_id,key=hist_id):
        st.session_state['thread_id'] = hist_id
        st.rerun()

thread_id = st.session_state['thread_id']
config = {"configurable":{"thread_id":thread_id}}


for msg in get_messages(thread_id):
        role ="user" if msg.type=="human" else "assistant"
        with st.chat_message(role):
            st.write(msg.content)




user_input = st.chat_input("Type here ")



import time

def fake_stream(text):
    for char in text:
        yield char
        time.sleep(0.002)

if user_input:
    with st.chat_message('user'):
        st.write(user_input)

    with st.chat_message('assistant'):
        with st.spinner("Thinking..."):
            ai_message = chatbot.invoke({"messages":[HumanMessage(content=user_input)]},config=config)
        st.write_stream(fake_stream(ai_message["messages"][-1].content))