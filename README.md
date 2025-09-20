# Web and Console Conversational AI Agent

**Web and Console Conversational AI Agent** is a dual-mode platform that provides both:

1. A **Web-based Voice Agent** (Django + WebSockets) for real-time conversational experiences.
2. A **Console-based Voice Agent** for lightweight, terminal-driven interactions.

This project combines cutting-edge **speech recognition (STT)**, **conversational AI (LLMs + RAG)**, and **text-to-speech (TTS)** for seamless, human-like dialogues.

---

## 🚀 Features

* **Speech Recognition (STT):**

  * Console: Faster-Whisper + OpenAI Whisper API
  * Web: Whisper API via Django Channels
* **Conversational AI:** GPT-4o-mini with context-aware memory
* **Text-to-Speech (TTS):**

  * Web: Edge-TTS (natural neural voices)
  * Console: pyttsx3 (offline fallback)
* **Retrieval-Augmented Generation (RAG):** LangChain + Chroma for knowledge-grounded responses
* **Web Interface:** Django + WebSockets for real-time interactions
* **Console Mode:** Portable, microphone-driven voice assistant

---

## 📂 Project Structure

```
web-and-console-conversational-ai-agent/
│── console_agent/                # Console-based bot
│   └── voice_agent_console.py
│
│── voiceai/                      # Django project
│── voiceai_app/                  # Django app
│── static/                       # Static assets
│── ecommerce_chroma_db/          # Chroma DB
│── requirements.txt
│── README.md
│── manage.py
│── db.sqlite3
```

---

## ⚙️ Installation

```bash
# Clone repo
git clone https://github.com/your-username/web-and-console-conversational-ai-agent.git
cd web-and-console-conversational-ai-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows

# Install dependencies
pip install -r requirements.txt
```

---

## ▶️ Running the Web Agent

```bash
# Run Django server
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) in your browser.
Make sure to set your `OPENAI_API_KEY` in `voiceai_app/API.env`.

---

## ▶️ Running the Console Agent

```bash
cd console_agent
python voice_agent_console.py
```

This starts the console-based bot that listens via microphone and responds with TTS.

---

## 📌 Requirements

* Python 3.9+
* Django + Django Channels
* LangChain
* Chroma
* OpenAI Python SDK
* Faster-Whisper
* Sounddevice
* Edge-TTS / pyttsx3
* Pydub
* gTTS

---


