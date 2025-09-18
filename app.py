import os
import time
import random
from datetime import datetime
import pandas as pd
import streamlit as st
import google.generativeai as genai

# ---------------- Config ----------------
LOCAL_LOG = "chat_logs.csv"
DEFAULT_MODEL = "gemini-1.5-flash"

# ---------------- Helpers ----------------
def get_gemini_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.environ.get("GEMINI_API_KEY")

def build_system_prompt(condition):
    """Define personality + style for each condition"""
    if condition == "acceptance":
        return (
            "You are 'Taylor', a warm and encouraging chat partner. "
            "Reply quickly with short, friendly sentences (1–3 sentences). "
            "Show genuine interest, supportive tone, maybe an emoji. "
        )
    elif condition == "ambiguous":
        return (
            "You are 'Sam', a somewhat neutral chat partner. "
            "Reply in a vague or hedgy way, not fully committed. "
            "Keep sentences short, sometimes noncommittal (e.g., 'maybe', 'not sure')."
        )
    elif condition == "rejection":
        return (
            "You are 'Casey', a distant and disinterested chat partner. "
            "Reply with curt, minimal responses (1–5 words). "
            "Tone should feel dismissive, cold, or unengaged."
        )
    else:
        return "You are a concise chat partner. Reply in short, clear sentences."

def generate_reply(api_key, user_text, condition, model=DEFAULT_MODEL, temp=0.7):
    genai.configure(api_key=api_key)
    system_prompt = build_system_prompt(condition)
    chat = genai.GenerativeModel(model)
    resp = chat.generate_content(
        f"{system_prompt}\n\nUser: {user_text}\nPartner:",
        generation_config=genai.types.GenerationConfig(
            temperature=temp,
            max_output_tokens=100
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

# Query params
qp = st.query_params
participant_id = qp.get("pid", [""])[0] or "anon"
condition = qp.get("condition", ["acceptance"])[0]  # acceptance / ambiguous / rejection

# Intro message by condition
intro_messages = {
    "acceptance": "Hey 👋 I’m Taylor. Excited to chat with you!",
    "ambiguous": "Hey, I’m Jordan. We can chat if you want, I guess.",
    "rejection": "Yeah, I’m Casey. What’s up.",
}
if "messages" not in st.session_state:
    st.session_state.messages = []
    t_intro = datetime.utcnow().isoformat()
    st.session_state.messages.append({"role": "bot", "text": intro_messages.get(condition, "Hi."), "time": t_intro})

# Chat input
user_input = st.text_input("You:", key="input")
if st.button("Send") and user_input.strip():
    t_user = datetime.utcnow().isoformat()
    st.session_state.messages.append({"role": "user", "text": user_input, "time": t_user})
    st.markdown(f"**You:** {user_input}")

    api_key = get_gemini_api_key()

    # Latency + typing style by condition
    if condition == "acceptance":
        delay = random.uniform(0.5, 1.0)
        with st.spinner("Partner is typing..."):
            time.sleep(delay)

    elif condition == "ambiguous":
        delay = random.uniform(5.0, 8.0)
        with st.spinner("Partner is typing..."):
            time.sleep(delay)

    elif condition == "rejection":
        delay = random.uniform(8.0, 12.0)
        # Simulate typing bubbles starting/stopping
        for _ in range(2):
            with st.spinner("Partner is typing..."):
                time.sleep(random.uniform(1.5, 3.0))
            time.sleep(random.uniform(0.5, 1.5))  # pause (no indicator)
        # Final actual typing period
        with st.spinner("Partner is typing..."):
            time.sleep(delay)

    else:
        delay = 1.0
        with st.spinner("Partner is typing..."):
            time.sleep(delay)

    reply = generate_reply(api_key, user_input, condition) if api_key else "[No API key found]"
    t_bot = datetime.utcnow().isoformat()

    st.session_state.messages.append({"role": "bot", "text": reply, "time": t_bot})
    st.markdown(f"**Partner:** {reply}")

    row = {
        "pid": participant_id,
        "user_time": t_user,
        "user_text": user_input,
        "bot_time": t_bot,
        "bot_text": reply,
        "condition": condition
    }
    append_log(row)

# Display history
st.markdown("---")
st.subheader("Chat history")
for m in st.session_state.messages:
    who = "You" if m["role"] == "user" else "Partner"
    st.write(f"**{who}** ({m['time']}): {m['text']}")
