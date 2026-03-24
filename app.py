import streamlit as st
from langchain_core.messages import BaseMessage,HumanMessage
from backend.chatbot import chatbot
from uuid import uuid4


#------------ Session Id / conversation id -------------------

if "thread_id" not in st.session_state:
    st.session_state['thread_id'] = str(uuid4())
thread_id = st.session_state['thread_id']


# --------------------------- message state and thread_id's conversation history ------------------------

if "message_state" not in st.session_state:
    st.session_state['message_state'] = {}


st.sidebar.header("LangGraph chatbot")
if st.sidebar.button("new chat"):
    thread_id=str(uuid4())


if thread_id not in st.session_state['message_state']:
    st.session_state['message_state'][thread_id] = []



keys = list(st.session_state["message_state"].keys())
st.sidebar.header("Chat history")
for idx in range(len(keys)):
    hist_id = keys[-(idx+1)]
    if st.sidebar.button(hist_id):
        st.session_state['thread_id']=hist_id

thread_id = st.session_state['thread_id']
config = {"configurable":{"thread_id":thread_id}}


for message in st.session_state['message_state'][thread_id]:
        with st.chat_message(message['role']):
            st.write(message['content'])




user_input = st.chat_input("Type here ")

if user_input:
    st.session_state['message_state'][thread_id].append({'role':'user',"content":user_input})
    with st.chat_message('user'):
        st.write(user_input)

    with st.chat_message('assistant'):
        ai_message = st.write_stream(messages_chunk.content for messages_chunk,metadata in chatbot.stream({"messages":[HumanMessage(content=user_input)]},config=config,stream_mode='messages'))
    st.session_state['message_state'][thread_id].append({'role':'assistant',"content":ai_message})