import sys
import os
import tkinter as tk
from tkinter import scrolledtext
import threading

# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

# --------------------------------------------------
# IMPORT CONFIG
# --------------------------------------------------

try:
    from config import MODEL_NAME, SYSTEM_PROMPT
except ImportError:
    from offline_chatbot.config import MODEL_NAME, SYSTEM_PROMPT


# --------------------------------------------------
# IMPORT OLLAMA CLIENT
# --------------------------------------------------

try:
    from ollama_client import generate_response
except ImportError:
    from chatbot.ollama_client import generate_response


# --------------------------------------------------
# CHAT MEMORY
# --------------------------------------------------

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


# --------------------------------------------------
# SEND USER PROMPT
# --------------------------------------------------

def send_prompt():

    prompt = user_box.get("1.0", tk.END).strip()

    if not prompt:
        return

    # Display user message
    chat_screen.config(state=tk.NORMAL)

    chat_screen.insert(
        tk.END,
        f"\nYou:\n{prompt}\n",
        "user"
    )

    chat_screen.config(state=tk.DISABLED)

    chat_screen.see(tk.END)

    # Clear input
    user_box.delete("1.0", tk.END)

    # Save conversation
    messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # Disable send button
    send_btn.config(state=tk.DISABLED)

    # Run AI in background
    threading.Thread(
        target=get_ai_response,
        daemon=True
    ).start()


# --------------------------------------------------
# AI RESPONSE
# --------------------------------------------------

def get_ai_response():

    try:

        answer = generate_response(
            MODEL_NAME,
            messages
        )

        messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        # Update UI safely using main thread
        root.after(
            0,
            display_ai_response,
            answer
        )

    except Exception as e:

        root.after(
            0,
            display_ai_response,
            f"AI Error: {str(e)}"
        )


# --------------------------------------------------
# DISPLAY AI RESPONSE
# --------------------------------------------------

def display_ai_response(answer):

    chat_screen.config(state=tk.NORMAL)

    chat_screen.insert(
        tk.END,
        f"\nAI Interviewer:\n{answer}\n",
        "bot"
    )

    chat_screen.config(state=tk.DISABLED)

    chat_screen.see(tk.END)

    send_btn.config(state=tk.NORMAL)


# --------------------------------------------------
# MAIN WINDOW
# --------------------------------------------------

root = tk.Tk()

root.title(
    "Battu Professional Mock Interviewer"
)

root.geometry(
    "700x750"
)

root.configure(
    bg="#212121"
)


# --------------------------------------------------
# CHAT SCREEN
# --------------------------------------------------

chat_screen = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD,
    bg="#1e1e1e",
    fg="#ffffff",
    font=("Segoe UI", 11),
    padx=10,
    pady=10
)

chat_screen.pack(
    padx=10,
    pady=10,
    fill=tk.BOTH,
    expand=True
)


# --------------------------------------------------
# USER MESSAGE STYLE
# --------------------------------------------------

chat_screen.tag_config(
    "user",
    foreground="#64b5f6",
    font=("Segoe UI", 11, "bold")
)


# --------------------------------------------------
# AI MESSAGE STYLE
# --------------------------------------------------

chat_screen.tag_config(
    "bot",
    foreground="#81c784",
    font=("Segoe UI", 11)
)


chat_screen.config(
    state=tk.DISABLED
)


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------

user_box = tk.Text(
    root,
    height=4,
    bg="#2d2d2d",
    fg="#ffffff",
    font=("Segoe UI", 11),
    insertbackground="white",
    wrap=tk.WORD
)

user_box.pack(
    padx=10,
    pady=5,
    fill=tk.X
)


# --------------------------------------------------
# SEND BUTTON
# --------------------------------------------------

send_btn = tk.Button(
    root,
    text="SEND",
    command=send_prompt,
    bg="#1976d2",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    relief=tk.FLAT,
    cursor="hand2"
)

send_btn.pack(
    padx=10,
    pady=(5, 10),
    fill=tk.X
)


# --------------------------------------------------
# START APPLICATION
# --------------------------------------------------

root.mainloop()
