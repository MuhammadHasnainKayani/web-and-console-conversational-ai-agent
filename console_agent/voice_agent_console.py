
import sounddevice as sd
import webrtcvad
import numpy as np
import queue
import io
import wave
from faster_whisper import WhisperModel
from openai import OpenAI
import requests
import time

import sounddevice as sd
import numpy as np
import requests

import pyttsx3

# Initialize the engine once (global)
tts_engine = pyttsx3.init()

def play_tts_streaming(text):
    print("🔊 TTS Playing ...")

    # Optional: tweak speed and voice
    tts_engine.setProperty('rate', 200)  # speaking speed (default ~200)
    tts_engine.setProperty('volume', 1.0)  # volume (0.0 to 1.0)

    voices = tts_engine.getProperty('voices')
    if voices:
        tts_engine.setProperty('voice', voices[0].id)  # select the first available voice

    tts_engine.say(text)     # queue the text to speak
    tts_engine.runAndWait()  # block until finished


openai_client = OpenAI(api_key='')

# ────────────── Configurations ──────────────
SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
VAD_MODE = 3
END_SILENCE_MS = 800
END_SILENCE_FRAMES = END_SILENCE_MS // FRAME_DURATION_MS

# ────────────── Globals & Initialization ──────────────
q_audio = queue.Queue()
vad = webrtcvad.Vad(VAD_MODE)
model = WhisperModel("base.en", device="cpu", compute_type="int8")
full_transcript = [
    {
        "role": "system",
        "content": """You are Medicare Benefits Assistant calling about 2025 coverage.
Maintain friendly professionalism. Never argue. Use simple Medicare terms. Transition smoothly between questions."""
    }
]

def callback(indata, frames, time, status):
    q_audio.put(indata.copy())


def frame_generator():
    while True:
        data = q_audio.get()
        audio_int16 = (data[:, 0] * 32767).astype(np.int16)
        yield audio_int16.tobytes(), audio_int16

def transcribe(audio_np):
     buf = io.BytesIO()
     with wave.open(buf, 'wb') as wf:
         wf.setnchannels(1)
         wf.setsampwidth(2)
         wf.setframerate(SAMPLE_RATE)
         wf.writeframes(audio_np.tobytes())
     buf.seek(0)
     buf.name = "audio.wav"

     resp = openai_client.audio.transcriptions.create(
         model="whisper-1",
         file=buf,
         response_format="text"
     )
     return resp.strip()

# def play_tts_streaming(text):
#     print("🔊 Streaming TTS in real-time...")
#     url = "https://api.openai.com/v1/audio/speech"
#     headers = {"Authorization": f"Bearer {openai_client.api_key}"}
#     payload = {
#         "model": "tts-1",
#         "input": text,
#         "voice": "alloy",
#         "response_format": "pcm",
#         "speed": 1.0
#     }
#     response = requests.post(url, headers=headers, json=payload, stream=True)
#     response.raise_for_status()
#
#     SAMPLE_RATE = 24000
#     SAMPLE_SIZE_BYTES = 2
#     buffer = bytearray()
#
#     with sd.OutputStream(
#         samplerate=SAMPLE_RATE, channels=1, dtype='int16',
#         blocksize=1024, latency='low'
#     ) as stream:
#         for chunk in response.iter_content(chunk_size=4096):
#             if not chunk:
#                 continue
#             buffer.extend(chunk)
#             num_bytes = (len(buffer)//SAMPLE_SIZE_BYTES)*SAMPLE_SIZE_BYTES
#             if num_bytes == 0:
#                 continue
#             samples = np.frombuffer(buffer[:num_bytes], dtype=np.int16)
#             stream.write(samples)
#             del buffer[:num_bytes]

def main():
    print("▶️  Listening (end-of-turn after ~0.8s silence)...\n")
    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1,
        blocksize=FRAME_SIZE, callback=callback
    ):
        silence_frames = 0
        voice_frames   = []
        in_speech      = False

        for pcm_bytes, audio_np in frame_generator():
            is_speech = vad.is_speech(pcm_bytes, SAMPLE_RATE)

            if is_speech:
                voice_frames.append(audio_np)
                silence_frames = 0
                in_speech = True
            else:
                if in_speech:
                    silence_frames += 1
                    if silence_frames > END_SILENCE_FRAMES:
                        full_audio = np.concatenate(voice_frames, axis=0)

                        # Transcription via Whisper-1 API
                        t0 = time.time()
                        transcription = transcribe(full_audio)
                        t1 = time.time()
                        print(f"Full Transcript: {transcription}")
                        full_transcript.append({
                            "role": "user", "content": transcription
                        })

                        # Chat completion
                        response = openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=full_transcript
                        )
                        reply = response.choices[0].message.content.strip()
                        t2 = time.time()
                        print(f"AI: {reply}")
                        full_transcript.append({
                            "role": "assistant", "content": reply
                        })

                        # TTS playback
                        play_t0 = time.time()
                        play_tts_streaming(reply)
                        play_t1 = time.time()

                        print(
                            f"[TIMING] STT: {t1-t0:.2f}s | Chat: {t2-t1:.2f}s | "
                            f"TTS: {play_t1-play_t0:.2f}s"
                        )

                        voice_frames = []
                        silence_frames = 0
                        in_speech = False
                        print("▶️  Ready for next utterance...\n")

if __name__ == "__main__":
    play_tts_streaming("Hi, my name is John. Can you hear me?")
    main()