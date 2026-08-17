import os
import requests
import streamlit as st
from pypdf import PdfReader

# --------------------------------------------------
# GROQ IMPORT
# --------------------------------------------------

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Battu's Mock Interviewer",
    page_icon="🎙️",
    layout="wide"
)


# --------------------------------------------------
# SYSTEM PROMPT
# --------------------------------------------------

SYSTEM_PROMPT = """
You are Battu's Professional Technical Mock Interviewer.

Candidate Experience:
4.5 years of Software Engineering experience.

Candidate Skills:
Python, Java, SQL, Data Analytics, Machine Learning,
Deep Learning and Generative AI.

Interview Rules:

1. Ask only ONE question at a time.
2. Ask technical, practical and scenario-based questions.
3. After the candidate answers:
   - Evaluate the answer.
   - Mention what was correct.
   - Mention what was missing.
   - Give a score out of 10.
   - Ask the next question.
4. Keep responses concise and professional.
5. Use the candidate's resume when available.
6. Gradually increase the difficulty.
7. Do not ask multiple questions at once.
8. Behave like a real technical interviewer.
9. If the answer is incorrect, explain the correct concept briefly.
10. Focus on interview-relevant knowledge.
"""


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>

    .stApp {
        background: linear-gradient(
            135deg,
            #e0f2fe 0%,
            #bae6fd 50%,
            #7dd3fc 100%
        );
    }

    section[data-testid="stSidebar"] {
        background-color: #ec4899;
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
        font-weight: 600 !important;
    }

    .stChatMessage {
        background: white !important;
        border: 2px solid #38bdf8 !important;
        border-radius: 16px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
    }

    .stChatMessage p {
        color: black !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
    }

    div[data-baseweb="input"] input {
        color: black !important;
        background-color: white !important;
        font-size: 16px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("🎙️ BattuDev AI Settings")

uploaded_file = st.sidebar.file_uploader(
    "Upload Resume (PDF)",
    type=["pdf"]
)


# --------------------------------------------------
# RESUME EXTRACTION
# --------------------------------------------------

resume_text = ""

if uploaded_file is not None:

    try:

        reader = PdfReader(uploaded_file)

        for page in reader.pages:

            text = page.extract_text()

            if text:
                resume_text += text + "\n"

        st.sidebar.success(
            "Resume uploaded successfully!"
        )

    except Exception as e:

        st.sidebar.error(
            f"Error reading resume: {e}"
        )


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title(
    "🎙️ Battu's Mock Interviewer"
)

st.caption(
    "AI-Powered Technical Mock Interviewer | "
    "Groq + Ollama"
)


# --------------------------------------------------
# DISPLAY CHAT HISTORY
# --------------------------------------------------

for message in st.session_state.messages:

    if message["role"] == "system":
        continue

    with st.chat_message(
        message["role"]
    ):

        st.write(
            message["content"]
        )


# --------------------------------------------------
# AI RESPONSE FUNCTION
# --------------------------------------------------

def get_ai_response():

    # --------------------------------------------------
    # RESUME CONTEXT
    # --------------------------------------------------

    resume_context = ""

    if resume_text:

        resume_context = f"""
Candidate Resume:

{resume_text}

Use this resume when asking relevant interview questions.
Do not repeat the entire resume in your response.
"""


    # --------------------------------------------------
    # GROQ API KEY
    # --------------------------------------------------

    api_key = None

    try:

        api_key = (
            st.secrets.get("GROQ_API_KEY")
            or os.getenv("GROQ_API_KEY")
        )

    except Exception:

        api_key = os.getenv(
            "GROQ_API_KEY"
        )


    # --------------------------------------------------
    # CLOUD ENGINE - GROQ
    # --------------------------------------------------

    if HAS_GROQ and api_key:

        try:

            client = Groq(
                api_key=api_key
            )

            groq_messages = []

            # System message
            groq_messages.append(
                {
                    "role": "system",
                    "content":
                        SYSTEM_PROMPT +
                        "\n" +
                        resume_context
                }
            )

            # Conversation history
            for message in st.session_state.messages:

                if message["role"] in [
                    "user",
                    "assistant"
                ]:

                    groq_messages.append(
                        {
                            "role": message["role"],
                            "content": message["content"]
                        }
                    )


            completion = client.chat.completions.create(

                model="llama-3.1-8b-instant",

                messages=groq_messages,

                temperature=0.3,

                max_tokens=500
            )


            return (
                completion
                .choices[0]
                .message
                .content
            )


        except Exception as e:

            groq_error = str(e)

    else:

        groq_error = (
            "Groq API key not configured."
        )


    # --------------------------------------------------
    # LOCAL ENGINE - OLLAMA
    # --------------------------------------------------

    try:

        conversation = ""

        for message in st.session_state.messages:

            if message["role"] == "user":

                conversation += (
                    f"\nCandidate:\n"
                    f"{message['content']}\n"
                )

            elif message["role"] == "assistant":

                conversation += (
                    f"\nInterviewer:\n"
                    f"{message['content']}\n"
                )


        prompt = f"""
{SYSTEM_PROMPT}

{resume_context}

Previous Interview Conversation:

{conversation}

Continue the interview from the current conversation.

Important:
- Evaluate the candidate's latest answer.
- Give a score out of 10.
- Explain briefly what was correct.
- Explain briefly what was missing.
- Ask exactly ONE next interview question.
"""


        response = requests.post(

            "http://localhost:11434/api/generate",

            json={
                "model": "qwen2.5:0.5b",
                "prompt": prompt,
                "stream": False
            },

            timeout=120
        )


        if response.status_code == 200:

            return response.json().get(
                "response",
                "No response received from Ollama."
            )


        return (
            "AI Engine Error.\n\n"
            f"Groq Error: {groq_error}\n"
            f"Ollama HTTP Status: "
            f"{response.status_code}"
        )


    except Exception as e:

        return (
            "Both AI engines are unavailable.\n\n"
            f"Groq Error: {groq_error}\n"
            f"Ollama Error: {str(e)}"
        )


# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

user_prompt = st.chat_input(
    "Type your interview answer..."
)


# --------------------------------------------------
# PROCESS USER INPUT
# --------------------------------------------------

if user_prompt:

    # Save user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_prompt
        }
    )


    # Display user message
    with st.chat_message("user"):

        st.write(
            user_prompt
        )


    # Generate AI response
    with st.chat_message("assistant"):

        with st.spinner(
            "AI is evaluating your answer..."
        ):

            ai_reply = get_ai_response()


        st.write(
            ai_reply
        )


    # Save AI response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": ai_reply
        }
    )
