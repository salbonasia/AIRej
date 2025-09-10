import os
import time
import random
from datetime import datetime
import pandas as pd
import streamlit as st
import google.generativeai as genai

# ---------------- Config ----------------
LOCAL_LOG = "chat_logs.csv"
DEFAULT_MODEL = "gemini-1.5-flash"   # free-tier model

# ---------------- Helpers ----------------
def get_gemini_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.environ.get("GEMINI_API_KEY")

def build_system_prompt(persona):
    if persona == "ai_clear":
        return (
            "You are 'Aria', an AI chatbot. Be clearly an AI but reply naturally and concisely. "
            "Use 1–3 sentences, no jargon, no 'As an AI' phrasing."
        )
    elif persona == "friend_like":
        return (
            "You are 'Alex', a casual, warm friend. Reply in short, conversational sentences "
            "(1–3 sentences). Be supportive, casual, maybe an emoji."
        )
    else:
        return "You are a concise chat partner. Reply using short, clear sentences."

def generate_reply(api_key, user_text, persona, model=DEFAULT_MODEL, temp=0.7):
    genai.configure(api_key=api_key)
    system_prompt = build_system_prompt(persona)
    chat = genai.GenerativeModel(model)
    resp = chat.generate_content(
        f"{system_prompt}\n\nUser: {user_text}\nPartner:",
        generation_config=genai.types.GenerationConfig(
            temperature=temp,
            max_output_tokens=120
        )
    )
    return resp.text.strip() if resp and resp.text else "[No response]"

def append_log(row):
    df = pd.DataFrame([row])
    if not os.path.exists(LOCAL_LOG):
        df.to_csv(LOCAL_LOG, index=False)
    else:
        df.to_csv(LOCAL_LOG, mode="a", header=False, index=False)

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Chatbot Experiment Demo", layout="centered")
st.title("Chatbot Experiment Demo")

# Grab participant info from URL
qp = st.query_params
participant_id = qp.get("pid", [""])[0] or "anon"
persona = qp.get("persona", ["ai_clear"])[0]
latency = qp.get("latency", ["fast"])[0]

# Initialize chat state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add intro message
    intro_msg = "Hi 👋 I’m your chat partner. Ready to talk?"
    t_intro = datetime.utcnow().isoformat()
    st.session_state.messages.append({"role": "bot", "text": intro_msg, "time": t_intro})

# Chat input
user_input = st.text_input("You:", key="input")
if st.button("Send") and user_input.strip():
    t_user = datetime.utcnow().isoformat()
    st.session_state.messages.append({"role": "user", "text": user_input, "time": t_user})
    st.markdown(f"**You:** {user_input}")

    # Latency condition
    if latency == "fast":
        delay = random.uniform(0.5, 1.0)
    elif latency == "slow":
        delay = random.uniform(4.0, 7.0)
    else:  # ambiguous
        delay = random.uniform(8.0, 12.0)

    with st.spinner("Partner is typing..."):
        time.sleep(delay)

    api_key = get_gemini_api_key()
    reply = generate_reply(api_key, user_input, persona) if api_key else "[No API key found]"
    t_bot = datetime.utcnow().isoformat()

    st.session_state.messages.append({"role": "bot", "text": reply, "time": t_bot})
    st.markdown(f"**Partner:** {reply}")

    # Log row
    row = {
        "pid": participant_id,
        "user_time": t_user,
        "user_text": user_input,
        "bot_time": t_bot,
        "bot_text": reply,
        "persona": persona,
        "latency": latency
    }
    append_log(row)

# Display history
st.markdown("---")
st.subheader("Chat history")
for m in st.session_state.messages:
    who = "You" if m["role"] == "user" else "Partner"
    st.write(f"**{who}** ({m['time']}): {m['text']}")
