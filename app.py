import streamlit as st
from langchain_core.messages import BaseMessage,HumanMessage
from backend.chatbot import chatbot
from uuid import uuid4
if "thread_id" not in st.session_state:
    st.session_state['thread_id'] = str(uuid4())
config = {"configurable":{"thread_id":st.session_state['thread_id']}}
if "message_state" not in st.session_state:
    st.session_state['message_state'] = []




for message in st.session_state['message_state']:
        with st.chat_message(message['role']):
            st.write(message['content'])




user_input = st.chat_input("Type here ")

if user_input:
    st.session_state['message_state'].append({'role':'user',"content":user_input})
    with st.chat_message('user'):
        st.write(user_input)

    with st.chat_message('assistant'):
        ai_message = st.write_stream(messages_chunk.content for messages_chunk,metadata in chatbot.stream({"messages":[HumanMessage(content=user_input)]},config=config,stream_mode='messages'))
    st.session_state['message_state'].append({'role':'assistant',"content":ai_message})