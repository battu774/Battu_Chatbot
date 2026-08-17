import sys
import os
import tkinter as tk
from tkinter import scrolledtext
import threading

# Path fix for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from config import MODEL_NAME, SYSTEM_PROMPT
except ImportError:
    from offline_chatbot.config import MODEL_NAME, SYSTEM_PROMPT

try:
    from ollama_client import generate_response
except ImportError:
    from chatbot.ollama_client import generate_response

# Global chat context
messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def send_prompt():
    prompt = user_box.get("1.0", tk.END).strip()
    if not prompt:
        return
    
    chat_screen.config(state=tk.NORMAL)
    chat_screen.insert(tk.END, f"\nMeeru:\n{prompt}\n", "user")
    user_box.delete("1.0", tk.END)
    chat_screen.config(state=tk.DISABLED)
    chat_screen.see(tk.END)
    
    messages.append({"role": "user", "content": prompt})
    threading.Thread(target=get_ai_response, daemon=True).start()

def get_ai_response():
    answer = generate_response(MODEL_NAME, messages)
    messages.append({"role": "assistant", "content": answer})
    
    chat_screen.config(state=tk.NORMAL)
    chat_screen.insert(tk.END, f"\nAI Assistant:\n{answer}\n", "bot")
    chat_screen.see(tk.END)
    chat_screen.config(state=tk.DISABLED)

# Desktop UI
root = tk.Tk()
root.title("Battu Personal Chatbot")
root.geometry("600x700")
root.configure(bg="#212121")

chat_screen = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="#1e1e1e", fg="#ffffff", font=("Segoe UI", 11))
chat_screen.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
chat_screen.tag_config("user", foreground="#64b5f6", font=("Segoe UI", 11, "bold"))
chat_screen.tag_config("bot", foreground="#81c784", font=("Segoe UI", 11))
chat_screen.config(state=tk.DISABLED)

user_box = tk.Text(root, height=3, bg="#2d2d2d", fg="#ffffff", font=("Segoe UI", 11), insertbackground="white")
user_box.pack(padx=10, pady=5, fill=tk.X)

send_btn = tk.Button(root, text="SEND", command=send_prompt, bg="#1976d2", fg="white", font=("Segoe UI", 10, "bold"))
send_btn.pack(padx=10, pady=(5, 10), fill=tk.X)

root.mainloop()

api_key = st.secrets.get("GROQ_API_KEY")