import speech_recognition as sr
from gtts import gTTS
import os
import uuid

# =========================
# 📁 AUDIO STORAGE FOLDER
# =========================
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# =========================
# 🎤 SPEECH → TEXT
# =========================
def speech_to_text(audio_file):
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)
        return text

    except sr.UnknownValueError:
        return "❌ Could not understand audio"

    except sr.RequestError:
        return "❌ Speech service unavailable"

    except Exception as e:
        print("Speech error:", e)
        return "❌ Error processing audio"


# =========================
# 🔊 TEXT → SPEECH
# =========================
def text_to_speech(text, lang="en"):
    """Generate TTS audio using gTTS. Returns the filename (not full path)."""
    try:
        if not text:
            return None

        # Strip plain text from any HTML tags before sending to TTS
        import re
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        if not clean_text:
            return None

        filename = f"response_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        tts = gTTS(text=clean_text, lang=lang)
        tts.save(filepath)
        print(f"[TTS] Saved audio for lang='{lang}': {filepath}")
        return filename

    except Exception as e:
        print(f"[TTS] Error for lang '{lang}': {e}")
        # Fallback to English if the specific language fails
        try:
            filename = f"response_{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(AUDIO_DIR, filename)
            tts = gTTS(text=clean_text, lang='en')
            tts.save(filepath)
            print(f"[TTS] Fallback to English: {filepath}")
            return filename
        except Exception as e2:
            print(f"[TTS] Fallback also failed: {e2}")
            return None