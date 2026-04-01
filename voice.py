import speech_recognition as sr
from gtts import gTTS
import os
import uuid

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
    try:
        # 🔥 unique filename (avoids overwrite)
        filename = f"response_{uuid.uuid4().hex}.mp3"

        tts = gTTS(text=text, lang=lang)
        tts.save(filename)

        return filename

    except Exception as e:
        print("TTS error:", e)
        return None