import streamlit as st
from langchain_core.messages import HumanMessage
from backend.chatbot import chatbot
from uuid import uuid4
import sqlite3
import os
import time

# ===================== DB SETUP =====================
DB_PATH = "chatbot.db"

def createlogin_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userName TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def register_user(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (userName, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False

def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE userName=? AND password=?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()
    return user


# ===================== AUTH UI =====================
createlogin_db()

st.title("Welcome to AI Chatbot")

if "user" not in st.session_state:
    entry_type = st.selectbox("Login / Sign Up", ["Login", "Sign-Up"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if entry_type == "Sign-Up":
        if st.button("Create Account"):
            if register_user(username, password):
                st.success("Account created. Please login.")
            else:
                st.error("Username already exists")

    else:
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state["user"] = username
                st.success("Logged in successfully")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()


# ===================== SESSION / THREAD =====================
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = f"{st.session_state['user']}_{uuid4()}"

thread_id = st.session_state["thread_id"]


# ===================== FETCH THREADS =====================
def get_all_threads():
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='checkpoints'
    """)

    if not cursor.fetchone():
        conn.close()
        return []

    cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
    rows = cursor.fetchall()
    conn.close()

    user = st.session_state["user"]

    # 👇 Only return user's chats
    return [r[0] for r in rows if r[0].startswith(user)]


# ===================== GET MESSAGES =====================
def get_messages(thread_id):
    state = chatbot.get_state(
        config={"configurable": {"thread_id": thread_id}}
    )
    return state.values.get("messages", [])


# ===================== SIDEBAR =====================
st.sidebar.header(f"User: {st.session_state['user']}")

if st.sidebar.button("➕ New Chat"):
    st.session_state["thread_id"] = f"{st.session_state['user']}_{uuid4()}"
    st.rerun()

if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

st.sidebar.header("Chat History")

keys = get_all_threads()

if not keys:
    st.sidebar.write("No chats yet")

for idx in range(len(keys)):
    hist_id = keys[-(idx + 1)]
    if st.sidebar.button(hist_id, key=hist_id):
        st.session_state["thread_id"] = hist_id
        st.rerun()


# ===================== CHAT UI =====================
config = {"configurable": {"thread_id": thread_id}}

for msg in get_messages(thread_id):
    role = "user" if msg.type == "human" else "assistant"
    with st.chat_message(role):
        st.write(msg.content)


# ===================== INPUT =====================
user_input = st.chat_input("Type your message...")


def fake_stream(text):
    for char in text:
        yield char
        time.sleep(0.002)


if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ai_message = chatbot.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config
            )

        st.write_stream(fake_stream(ai_message["messages"][-1].content))