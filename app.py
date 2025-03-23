import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sounddevice as sd
import queue
import json
import vosk
import threading

# ---- Streamlit UI setup ----
st.set_page_config(page_title="Wake Word Assistant", layout="centered")
st.title("🎙️ Wake Word Assistant")

status_placeholder = st.empty()
log_placeholder = st.empty()

# ---- Auto refresh ----
st_autorefresh(interval=1000, limit=None)

# ---- Global state ----
shared_state = {
    "wake_detected": False,
    "status": "🔴 Waiting for wake word...",
    "log": [],
}

# ---- Wake words ----
wake_words = ["hey", "hi", "hello"]

# ---- Audio setup ----
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    audio_queue.put(bytes(indata))

def process_audio():
    model = vosk.Model(lang="en-us")
    recognizer = vosk.KaldiRecognizer(model, 16000)
    
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        while True:
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                detected_text = result.get("text", "").strip().lower()
                
                # ONLY respond if detected_text EXACTLY matches a wake word
                if detected_text in wake_words:
                    shared_state["wake_detected"] = True
                    shared_state["status"] = f"🟢 Wake word '{detected_text}' detected! How can I help you?"
                    shared_state["log"].append(f"🟢 Wake word '{detected_text}' detected!")
                else:
                    # ignore non-wake words entirely (no terminal print, no UI update)
                    continue

# ---- Start background thread (once) ----
if "thread_running" not in st.session_state:
    threading.Thread(target=process_audio, daemon=True).start()
    st.session_state.thread_running = True

# ---- Update Streamlit UI ----
status_placeholder.markdown(f"**Status:** {shared_state['status']}")

# Display log (last 5 detections)
log_placeholder.markdown("\n\n".join(shared_state["log"][-5:]))

