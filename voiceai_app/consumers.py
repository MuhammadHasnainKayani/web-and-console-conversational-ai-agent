# chat/consumers.py
import json
import os
import uuid
import tempfile
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.conf import settings
# ---------------------------
# Import and configure pipeline modules
# ---------------------------
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import AIMessage, HumanMessage
from langchain.prompts import ChatPromptTemplate
from gtts import gTTS  # Google Text-to-Speech
from pydub import AudioSegment
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv

# Load environment variables (adjust the path as needed)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'API.env'))
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY is missing in your env file.")

# ---------------------------
# Global initialization for LangChain components
# ---------------------------


try:
     # Initialize Vector DB and LLM
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vector_db_path = os.path.join(BASE_DIR, "voiceai_app", "almaarifah_chroma_db")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
    vector_db = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)

except Exception as e:
    print(f"Error loading vector DB: {e}")

# Global chat history for the QA chain
chat_history_global = []

llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=api_key, temperature=0.7)

# Setup condense question prompt for history-aware retriever
condense_question_system_template = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)
condense_question_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", condense_question_system_template),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ]
)
history_aware_retriever = create_history_aware_retriever(
    llm, vector_db.as_retriever(), condense_question_prompt
)
system_prompt = (
   "You are a helpful and friendly voice assistant who responds in a conversational tone. "
    "Use the following retrieved context to answer the user's question in a natural, spoken style. "
    "If you are unsure of the answer, simply say 'Sorry I don't have have specific infor related to that.' Keep your response concise (up to three sentences) and engaging."
    "\n\n{context}"
)
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ]
)
qa_chain = create_stuff_documents_chain(llm, qa_prompt)
convo_qa_chain = create_retrieval_chain(history_aware_retriever, qa_chain)

# ---------------------------
# Asynchronous wrappers for each pipeline function
# ---------------------------

async def async_transcribe_audio(audio_path):
    """Convert WAV audio file to text using OpenAI's Whisper model."""

    def transcribe():
        from openai import OpenAI
        # Initialize OpenAI client for transcription
        client = OpenAI(api_key=api_key)

        with open(audio_path, "rb") as af:
            transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=af
)
            return transcription.text.strip()
    return await sync_to_async(transcribe)()
async def async_generate_response(user_text):
    """Generate a response using the QA chain with LangChain."""
    def process():
        # Append user message to global history
        chat_history_global.append(HumanMessage(content=user_text))
        
        # Use the conversation QA chain which handles retrieval and history
        response = convo_qa_chain.invoke({
            "input": user_text,
            "chat_history": chat_history_global[-10:]  # Last 10 messages
        })
        
        # Get the answer from the response
        result = response.get("answer", "Sorry, I couldn’t find relevant information.")
        
        # Append AI response to history
        chat_history_global.append(AIMessage(content=result))
        return result
    return await sync_to_async(process)()

import edge_tts

async def async_generate_tts(text):
    """
    Convert response text to speech (TTS) using edge-tts.
    Returns the path to the generated MP3 file.
    """
    temp_audio_path = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.mp3")
    communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural")
    await communicate.save(temp_audio_path)
    return temp_audio_path


async def async_increase_speed(audio_path, speed=1.25):
    """
    Increase the playback speed of an MP3 file using pydub.
    Returns the same file path with the modified audio.
    This function is optional—call it if you want to speed up the audio.
    """
    def increase_speed():
        audio = AudioSegment.from_file(audio_path, format="mp3")
        sped_audio = audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * speed)
        }).set_frame_rate(audio.frame_rate)
        sped_audio.export(audio_path, format="mp3")
        return audio_path
    return await sync_to_async(increase_speed)()

# ---------------------------
# The WebSocket Consumer (Pipeline)
# ---------------------------
class VoiceAgentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("WebSocket connection accepted.")

    async def disconnect(self, close_code):
        print("WebSocket disconnected with code:", close_code)

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            # Save the incoming audio data to a temporary file.
            # Expect a WAV file from the client.
            temp_input_path = os.path.join(tempfile.gettempdir(), f"input_{uuid.uuid4().hex}.wav")
            with open(temp_input_path, "wb") as f:
                f.write(bytes_data)
            try:
                # 1. Transcribe the audio.
                user_text = await async_transcribe_audio(temp_input_path)
                print("Transcription:", user_text)
                
                # 2. Generate responses using both pipelines.
                qa_response = await async_generate_response(user_text)
                final_response_text = qa_response
                print("Final Agent Response:", final_response_text)
                
                # 3. Convert the response text to speech (TTS).
                tts_audio_path = await async_generate_tts(final_response_text)
                # Optional: Increase speed (uncomment to use).
                # tts_audio_path = await async_increase_speed(tts_audio_path, speed=1.25)
                
                # 4. Read the generated audio and send it back as binary data.
                with open(tts_audio_path, "rb") as af:
                    tts_audio_data = af.read()
                await self.send(bytes_data=tts_audio_data)
            except Exception as e:
                error_msg = f"Error processing audio: {str(e)}"
                print(error_msg)
                await self.send(text_data=json.dumps({"error": error_msg}))
            finally:
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path)
        elif text_data:
            try:
                data = json.loads(text_data)
                message = data.get("message", "")
                response_text = f"Echo: {message}"
                await self.send(text_data=json.dumps({"response": response_text}))
            except Exception as e:
                await self.send(text_data=json.dumps({"error": str(e)}))
