import os
import sys
import requests
import threading
import streamlit as st
from pypdf import PdfReader

# 1. Dependency Handling
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# 2. Page Configuration
st.set_page_config(
    page_title="Battu's Mock Interviewer", 
    page_icon="🎙️", 
    layout="wide"
)

# 3. Custom Theme CSS
st.markdown("""
<style>
/* Main Background: Light Blue Gradient */
.stApp {
    background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 50%, #7dd3fc 100%) !important;
    color: #0f172a !important;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: #ec4899 !important;
}
section[data-testid="stSidebar"] * {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Chat Card Container */
.stChatMessage {
    background: #ffffff !important;
    border: 2px solid #38bdf8 !important;
    border-radius: 16px !important;
    padding: 16px !important;
    margin-bottom: 12px !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
}

/* Message Text Styling */
.stChatMessage p, .stChatMessage div, .stChatMessage span {
    color: #000000 !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    line-height: 1.6 !important;
}

/* Input Box Formatting */
div[data-baseweb="input"] input {
    color: #000000 !important;
    background-color: #ffffff !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# 4. Sidebar Content & Resume Upload
st.sidebar.title("BattuDev AI Settings")
uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type=["pdf"])

resume_text = ""
if uploaded_file is not None:
    try:
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                resume_text += text + "\n"
        st.sidebar.success("Resume Uploaded Successfully!")
    except Exception as e:
        st.sidebar.error("Error reading PDF file.")

# 5. Header Section
st.title("🎙️ Battu's Mock Interviewer")

# Initialize Chat Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Conversation History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 6. User Input Handling & Multi-Engine AI Inference
if user_prompt := st.chat_input("Type your answer or question here..."):
    # Render user message
    st.chat_message("user").write(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    ai_reply = ""
    
    # Construction of prompt context
    prompt_payload = user_prompt
    if resume_text:
        prompt_payload = f"Context Resume: {resume_text}\n\nUser Question/Answer: {user_prompt}"

    # Try Cloud Engine (Groq API)
    cloud_success = False
    try:
        api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
        if HAS_GROQ and api_key:
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a professional technical interviewer."},
                    {"role": "user", "content": prompt_payload}
                ],
                model="llama-3.3-70b-versatile"
            )
            ai_reply = chat_completion.choices[0].message.content
            cloud_success = True
        else:
            cloud_error_reason = "API Key missing in Secrets/Env."
    except Exception as cloud_err:
        cloud_error_reason = str(cloud_err)

    # Fallback to Local Engine (Ollama)
    if not cloud_success:
        try:
            payload = {
                "model": "qwen2.5:0.5b", 
                "prompt": prompt_payload, 
                "stream": False
            }
            resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=5)
            if resp.status_code == 200:
                ai_reply = resp.json().get("response", "No response from local Ollama.")
            else:
                ai_reply = f"Cloud Error ({cloud_error_reason}) & Local Ollama HTTP Error."
        except Exception:
            ai_reply = f"Cloud Error: {cloud_error_reason} | Local Ollama server is offline."

    # Render Assistant Response
    st.chat_message("assistant").write(ai_reply)
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})