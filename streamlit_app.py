import streamlit as st
import requests
import threading
import os
from pypdf import PdfReader

# Try importing dependencies
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

try:
    import pyttsx3
    HAS_VOICE = True
except ImportError:
    HAS_VOICE = False

# Page Setup
st.set_page_config(page_title="Battu's Mock Interviewer", page_icon="🎙️", layout="wide")

# 🎨 Custom Theme CSS (Light Blue Main + Pink Sidebar + High-Contrast Black Text)
st.markdown("""
    <style>
    /* Main Background: Light Blue Gradient */
    .stApp { 
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 50%, #7dd3fc 100%) !important; 
        color: #0f172a !important; 
    }
    
    /* Title Styling */
    .custom-title { 
        color: #0284c7 !important; 
        font-weight: 900 !important; 
        font-size: 2.8rem !important; 
        text-shadow: 0 2px 10px rgba(2, 132, 199, 0.2); 
    }

    /* Sidebar: Vibrant Pink Background */
    section[data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #ec4899 0%, #db2777 50%, #be185d 100%) !important; 
    }
    section[data-testid="stSidebar"] * { 
        color: #ffffff !important; 
        font-weight: 600 !important; 
    }

    /* Chat Card Container (Clear Visibility) */
    .stChatMessage { 
        background: #ffffff !important; 
        border: 2px solid #38bdf8 !important; 
        border-radius: 16px !important; 
        padding: 16px !important; 
        margin-bottom: 12px !important; 
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important; 
    }

    /* Message Text Styling - Pure Dark Black for Crisp Readability */
    .stChatMessage p, .stChatMessage div, .stChatMessage span { 
        color: #000000 !important; 
        font-size: 1.05rem !important; 
        font-weight: 600 !important; 
        line-height: 1.6 !important; 
    }

    /* Input Box Formatting - Fix for invisible typed text */
    div[data-baseweb="input"] input { 
        color: #000000 !important; 
        background-color: #ffffff !important; 
        font-size: 1rem !important; 
        font-weight: 600 !important; 
    }
    .stChatInputContainer {
        border: 2px solid #db2777 !important;
        border-radius: 12px !important;
        background-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# Voice Engine
def speak_offline(text):
    if not HAS_VOICE: return
    def run_tts():
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 170)
            engine.say(text)
            engine.runAndWait()
        except: pass
    threading.Thread(target=run_tts, daemon=True).start()

# Pink Sidebar Controls
with st.sidebar:
    st.header("⚙️ Control Panel")
    voice_enabled = st.checkbox("🔊 Enable Voice (Local Only)", value=True)
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    
    resume_text = ""
    if uploaded_file:
        pdf_reader = PdfReader(uploaded_file)
        resume_text = "".join([p.extract_text() for p in pdf_reader.pages])
        st.success("✅ Resume Loaded!")

# Main Header
st.markdown('<h1 class="custom-title">🎙️ Battu\'s Mock Interviewer</h1>', unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): 
        st.write(msg["content"])

# User Chat Input
if user_prompt := st.chat_input("Type your answer or question here..."):
    st.chat_message("user").write(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    ai_reply = ""
    
    # Try Cloud (Groq) API first
    try:
        api_key = st.secrets["GROQ_API_KEY"]
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Resume Text: {resume_text}\nQuery: {user_prompt}"}],
            model="llama-3.1-70b-versatile",
        )
        ai_reply = chat_completion.choices[0].message.content
    except Exception:
        # Fallback to Local Ollama
        payload = {"model": "qwen2.5:0.5b", "prompt": user_prompt, "stream": False}
        try:
            resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
            ai_reply = resp.json().get("response", "Error connecting to local Ollama.")
        except Exception:
            ai_reply = "API Key not found in cloud secrets and local Ollama server is offline."

    st.chat_message("assistant").write(ai_reply)
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
    
    if voice_enabled: 
        speak_offline(ai_reply)