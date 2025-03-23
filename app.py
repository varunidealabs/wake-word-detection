import streamlit as st

# Must be first Streamlit call
st.set_page_config(page_title="Voice Assistant", layout="centered")

from streamlit_autorefresh import st_autorefresh
import sounddevice as sd
import queue
import json
import vosk
import threading

# Wake words configuration
wake_words = ["hey", "hi", "hello"]

# Audio queue
q = queue.Queue()

# Shared state for thread-safe updates
shared_state = {
    "wake_detected": False,
    "last_detected_text": "",
    "status": "🔴 Waiting for wake word...",
}

# Auto-refresh Streamlit UI every second
st_autorefresh(interval=1000, limit=None, key="refresh")

# Streamlit UI
st.title("🎙️ Wake Word Assistant")
status_placeholder = st.empty()
detection_placeholder = st.empty()

# Audio callback function
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

# Background audio processing
def process_audio():
    model = vosk.Model(lang="en-us")
    recognizer = vosk.KaldiRecognizer(model, 16000)

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback,
    ):
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                text = json.loads(result).get("text", "").lower().strip()
                if text:
                    print(f"Detected: {text}")
                    shared_state["last_detected_text"] = text

                    # ONLY respond if wake word detected
                    if any(w in text.split() for w in wake_words):
                        shared_state["wake_detected"] = True
                        shared_state["status"] = "🟢 Wake word detected! How can I help you?"
                    else:
                        # Ignore non-wake words completely
                        shared_state["wake_detected"] = False
                        shared_state["status"] = "🔴 Waiting for wake word..."

# Start the audio processing thread once
if "thread_started" not in st.session_state:
    threading.Thread(target=process_audio, daemon=True).start()
    st.session_state.thread_started = True

# Update Streamlit UI based on wake word detection
status_placeholder.markdown(f"**Status:** {shared_state['status']}")

if shared_state["wake_detected"]:
    detection_placeholder.success(
        f"🤖 Wake word '**{shared_state['last_detected_text']}**' detected!"
    )
else:
    detection_placeholder.info("🎙️ Listening for wake word...")
