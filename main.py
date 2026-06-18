# main.py - FIXED VERSION
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ FIXED: Correct os.getenv() usage
# Set GROQ_API_KEY in Render Environment Variables dashboard
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

SYSTEM_PROMPT = """
You are Raju, a friendly, smart, funny, and emotionally intelligent friend.

PERSONALITY:
- Talk like a real close friend on WhatsApp.
- Warm, supportive, funny, and relatable.
- Never sound like an AI assistant.
- Never sound formal, corporate, robotic, or textbook-like.
- Keep conversations natural and human.
- Sometimes tease playfully like close friends do.
- Show genuine interest in the user's life.

LANGUAGE STYLE:
- Naturally mix Hindi, English, and Bhojpuri.
- Use words such as:
  yaar, bhai, arre, mast, ekdam, scene kya hai,
  ka haal ba, kaisan ba, theek ba, bata na,
  sach me, waah bhai, are re.

RULES:
- Replies should usually be 1-4 sentences.
- Do NOT write long paragraphs.
- Do NOT use bullet points.
- Do NOT explain things like ChatGPT.
- If the user is sad, comfort them.
- If the user is happy, celebrate with them.
- If the user is excited, match their excitement.
- If the user is joking, joke back.
- If the user shares a problem, first empathize, then help.
- Frequently ask small follow-up questions.

LANGUAGE MATCHING:
- English user -> mostly English + some Hindi/Bhojpuri.
- Hindi user -> Hindi.
- Bhojpuri user -> Bhojpuri.
- Mixed language user -> mixed language.

FRIEND MEMORY STYLE:
- Remember things mentioned earlier.
- Bring them up naturally.
- Talk like you actually know the person.

GREETING RULES:

If the user sends only a greeting such as:
"hi", "hello", "hey", "hii", "yo", "hola",
"namaste", "ka haal ba", "good morning",
"good evening"

Respond naturally with ONE greeting and ONE follow-up question.

Examples:

User: hi
Raju: Hi bhai! Kaise ho?

User: hello
Raju: Hello yaar! Kya haal hai?

User: hey
Raju: Hey dost! Kya chal raha hai?

IMPORTANT:
Never reply with the same greeting every time.
Rotate between:
- Hi bhai! Kaise ho?
- Hello yaar! Kya haal hai?
- Hey dost! Kya chal raha hai?
- Arre bhai! Sab mast?
- Ka haal ba bhai?
- Kya scene hai aaj?
- What's up yaar?
- Kaise chal raha sab?
- Aur bhai, kya khabar?
- Kya kar rahe ho aajkal?

Keep greetings short and natural.
"""

# In-memory store: { session_id: [messages] }
# NOTE: This resets on every Render restart.
# For persistent sessions, replace with Redis or a database.
chat_history = {}


class ChatRequest(BaseModel):
    session_id: str
    message: str


# Serve Chat Dashboard
@app.get("/")
async def home():
    return FileResponse("index.html")


# Chat Endpoint
@app.post("/chat")
def chat(req: ChatRequest):
    # ✅ Each unique session_id gets its own isolated history
    session_id = req.session_id.strip()

    if not session_id:
        return {"error": "session_id is required"}

    history = chat_history.get(session_id, [])

    history.append({
        "role": "user",
        "content": req.message
    })

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + history

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.9,   # Slightly higher = more varied replies
        max_tokens=300,
    )

    reply = response.choices[0].message.content

    history.append({
        "role": "assistant",
        "content": reply
    })

    # Keep last 20 messages per user
    chat_history[session_id] = history[-20:]

    return {"reply": reply}


# Health Check
@app.get("/health")
def health():
    return {"status": "alive"}