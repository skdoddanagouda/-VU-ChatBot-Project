from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rag import get_answer
from auth import AuthSystem
from attendance import AttendanceSystem
from timetable import TimetableSystem
from translator import translate_pipeline, from_english
from voice import text_to_speech
from emailrouter import send_email_to_admin

import pandas as pd
import os

app = FastAPI()

# =========================
# 🌐 CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# 📁 PATHS (FIXED)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # ✅ FIXED

attendance_path = os.path.join(BASE_DIR, "data", "attendance.xlsx")
timetable_path = os.path.join(BASE_DIR, "data", "timetable.xlsx")

# =========================
# 🔐 INIT SYSTEMS
# =========================
auth = AuthSystem()

attendance_df = pd.read_excel(attendance_path)
timetable_df = pd.read_excel(timetable_path)

attendance = AttendanceSystem(attendance_df)
timetable = TimetableSystem(timetable_df)

# =========================
# 🧠 SESSION STORE
# =========================
user_sessions = {}

# =========================
# 🏠 ROOT
# =========================
@app.get("/")
def home():
    return {"message": "VURA backend running 🚀"}

# =========================
# 💬 CHAT API
# =========================
@app.get("/chat")
def chat(query: str, user_id: str = "default", email: str = None):

    print("🔍 QUERY:", query)

    # =========================
    # 🌍 TRANSLATION PIPELINE
    # =========================
    english_query, user_lang = translate_pipeline(query)
    query_lower = english_query.lower()

    try:
        # =========================
        # 🔐 LOGIN
        # =========================
        user = None

        if query.isdigit() and len(query) >= 6:
            user = auth.login(query)

        elif len(query.split()) >= 2:
            user = auth.login(query)

        if user:
            user_sessions[user_id] = {
                "uen": user.get("uen"),
                "role": user["role"],
                "name": user.get("name"),
                "semester": user.get("semester"),
                "section": user.get("section"),
                "email": email,
                "lang": user_lang,
                "pending_query": None,
                "awaiting_email_permission": False
            }

            return {
                "response": f"Login successful as {user['role']} ✅",
                "language": user_lang
            }

        # =========================
        # 🔐 AUTH CHECK
        # =========================
        session = user_sessions.get(user_id)

        requires_auth = any(word in query_lower for word in [
            "attendance", "timetable", "schedule", "classroom"
        ])

        if requires_auth and not session:
            return {
                "response": "Please login first using your UEN or name.",
                "language": user_lang
            }

        # =========================
        # 📊 ATTENDANCE
        # =========================
        if "attendance" in query_lower and session:

            if session["role"] == "student":
                response_text = attendance.student_view(session["uen"])
            else:
                response_text = attendance.teacher_view(session["name"])

            final = from_english(str(response_text), user_lang)
            audio = text_to_speech(final, user_lang)

            return {
                "response": final,
                "language": user_lang,
                "audio": audio
            }

        # =========================
        # 📅 TIMETABLE
        # =========================
        if ("timetable" in query_lower or "schedule" in query_lower) and session:

            if session["role"] == "student":
                response_text = timetable.student_view(
                    session["semester"],
                    session["section"]
                )
            else:
                response_text = timetable.teacher_view(session["name"])

            final = from_english(str(response_text), user_lang)
            audio = text_to_speech(final, user_lang)

            return {
                "response": final,
                "language": user_lang,
                "audio": audio
            }

        # =========================
        # 🤖 RAG
        # =========================
        answer = get_answer(english_query)

        # =========================
        # 🚨 FALLBACK (EMAIL FLOW)
        # =========================
        if not answer or len(answer) < 15:

            if session and not session["awaiting_email_permission"]:
                session["pending_query"] = query
                session["awaiting_email_permission"] = True

                return {
                    "response": "I couldn't find an answer. Do you want me to send this to admin? (yes/no)",
                    "language": user_lang
                }

            if session and session["awaiting_email_permission"]:

                if "yes" in query_lower:

                    if not email:
                        return {
                            "response": "Please provide your email.",
                            "language": user_lang
                        }

                    send_email_to_admin(email, session["pending_query"])

                    session["awaiting_email_permission"] = False
                    session["pending_query"] = None

                    return {
                        "response": "✅ Query sent to admin successfully.",
                        "language": user_lang
                    }

                elif "no" in query_lower:

                    session["awaiting_email_permission"] = False
                    session["pending_query"] = None

                    return {
                        "response": "Okay, let me know if you need anything else.",
                        "language": user_lang
                    }

        # =========================
        # ✅ NORMAL RESPONSE
        # =========================
        final_answer = answer
        audio_file = text_to_speech(final_answer, user_lang)

        return {
            "response": final_answer,
            "language": user_lang,
            "audio": audio_file
        }

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {"error": str(e)}