from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from engine import get_answer, normalize_query
from auth import AuthSystem
from attendance import AttendanceSystem
from timetable import TimetableSystem
from translator import translate_pipeline, from_english, get_language_name
from voice import text_to_speech, AUDIO_DIR
from emailrouter import send_email_to_admin
from database import db_manager
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =========================
# 📁 PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "VidyashilaUniversity_SemII_Dataset.xlsx")
TIMETABLE_FILE = os.path.join(BASE_DIR, "data", "Timetable Sem-II_11-01-2026 updated.xlsx")
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

class AskRequest(BaseModel):
    question: str
    lang: str = "en"

app = FastAPI()

# =========================
# 🏠 SERVE FRONTEND (Root)
# =========================
@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        print(f"[OK] Serving frontend from: {index_path}")
        return FileResponse(index_path)
    print(f"[ERROR] Frontend NOT FOUND at: {index_path}")
    return {"message": "VURA backend online [OK]", "frontend_error": f"index.html not found at {index_path}"}

# Mount frontend directory for other assets
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Mount audio directory so generated MP3s can be fetched
if os.path.exists(AUDIO_DIR):
    app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# =========================
# 🌐 CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# 🔐 INIT SYSTEMS
# =========================
auth = AuthSystem()

try:
    attendance_df = pd.read_excel(DATA_FILE, sheet_name="Attendance Summary")
    attendance = AttendanceSystem(attendance_df)
except:
    attendance = None

try:
    timetable_df = pd.read_excel(TIMETABLE_FILE, sheet_name="BTECH-Sec I")
    timetable = TimetableSystem(timetable_df)
except:
    timetable = None

# =========================
# 🧠 SESSION STORE
# =========================
user_sessions = {}

# =========================
# 💬 API ENDPOINTS
# =========================
@app.get("/health")
def health():
    return {"status": "online"}

@app.get("/tts")
def tts_route(text: str, lang: str = "en"):
    """Standalone TTS endpoint — generates audio for any text/language pair."""
    try:
        # Truncate very long texts to avoid slow generation
        clean = re.sub(r'<[^>]+>', '', text).strip()[:600]
        filename = text_to_speech(clean, lang)
        if filename:
            return {"audio": filename}
    except Exception as e:
        print(f"[/tts] Error: {e}")
    return {"audio": None}

@app.get("/chat")
def chat(query: str, user_id: str = "default", email: str = None):
    # ✅ 1. Check if input is an email (for pending queries)
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    is_email = re.match(email_pattern, query.strip()) is not None
    
    session = user_sessions.get(user_id, {})
    
    if is_email and session.get("pending_query"):
        user_email = query.strip()
        pending_q = session["pending_query"]
        
        # Send email to admin
        send_email_to_admin(user_email, pending_q)
        
        # Clear pending
        session["pending_query"] = None
        user_sessions[user_id] = session
        
        response_msg = "Thank you! Your query and email have been forwarded to our team. We will get back to you soon."
        return {"response": response_msg, "language": "en"}

    # Proceed with translation first to establish language and query
    english_query, user_lang = translate_pipeline(query)
    query_lower = english_query.lower()

    # ✅ 2. Check if input is a Registration No (UEN)
    uen_pattern = r'^\d{4}UG\d{5,8}$'
    is_uen = re.match(uen_pattern, query.strip().upper()) is not None
    
    if is_uen:
        student = db_manager.get_student_info(query.strip().upper())
        if student:
            user_sessions[user_id] = {
                "uen": str(student.get("Registration No")),
                "name": str(student.get("Student Name")),
                "section": str(student.get("Section")),
                "semester": str(student.get("Semester")),
                "role": "student"
            }
            return {"response": f"Recognized student: {student.get('Student Name')}. You can now ask about your attendance, timetable, or teacher details.", "language": user_lang}
        else:
            return {"response": "I couldn't find a student with that Registration No. Please try again.", "language": user_lang}

    # Proceed with normal chat
    try:
        user = None
        if query.isdigit() and len(query) >= 6:
            user = auth.login(query)
        elif len(query.split()) >= 2:
            user = auth.login(query)

        if user:
            user_sessions[user_id] = {
                "uen": user.get("uen"), "name": user.get("name"), 
                "semester": user.get("semester"), "section": user.get("section"),
                "role": user["role"]
            }
            return {"response": f"Login successful as {user['role']} [OK]", "language": user_lang}

        # Robust session handling
        session = user_sessions.get(user_id, {})
        
        # Keywords detection (check raw input, English query, and normalized versions)
        protected_keywords = ["attendance", "timetable", "teacher", "class room", "classroom", "faculty"]
        raw_query_normalized = normalize_query(query)
        english_query_normalized = normalize_query(english_query)
        
        is_protected = any(w in raw_query_normalized for w in protected_keywords) or \
                      any(w in english_query_normalized for w in protected_keywords)
        
        if is_protected:
            if not session or "uen" not in session: 
                return {"response": "To provide specific details like attendance or classroom info, I need your Registration No. Please type your UEN (e.g., 2025UG000409).", "language": user_lang}
            
            # --- Attendance ---
            if "attendance" in query_lower:
                data = db_manager.get_attendance(session["uen"])
                if not data:
                    res = "No attendance records found for your account."
                else:
                    # Summarize attendance for all courses
                    summary = [f"- {d['Course Title']}: {d['Attendance %']}%" for d in data]
                    res = f"Here is your attendance summary for {session['name']}:\n" + "\n".join(summary)
            
            # --- Teacher / Classroom ---
            elif any(k in query_lower for k in ["teacher", "faculty", "classroom", "class room"]):
                data = db_manager.get_faculty_info(section=session["section"])
                if not data:
                    res = "Information about your teachers or classrooms is currently unavailable."
                else:
                    details = [f"- {d['Course Title']}: Prof. {d['Faculty Name']} in Room {d['Room']}" for d in data]
                    res = f"Details for your section ({session['section']}):\n" + "\n".join(details)
            
            # --- Timetable ---
            elif "timetable" in query_lower:
                data = db_manager.get_timetable(session["section"], session["semester"])
                if not data:
                    res = "Timetable not found for your section."
                else:
                    sheet_name = data.get("sheet", session["section"])
                    res = f"Your timetable (Sheet: {sheet_name}) has been found! You can now ask specific questions about your classes or view the full schedule."

            else:
                res = "I can help with attendance, timetables, and teacher details once you provide your UEN."

            final = from_english(str(res), user_lang)
            return {"response": final, "language": user_lang, "audio": text_to_speech(final, user_lang)}

        # Fallback to RAG
        # 🇮🇳 Map code to full name for the LLM prompt
        user_lang_name = get_language_name(user_lang)
        
        # Get answer in the target language
        answer = get_answer(english_query, user_lang=user_lang_name)
        
        # ✅ Check if unanswerable
        unanswerable_triggers = [
            "couldn't find accurate information",
            "provide your mail",
            "provide your email"
        ]
        if any(trigger in answer.lower() for trigger in unanswerable_triggers):
            # Store the ORIGINAL query (before translation) for context
            if session is None: session = {}
            session["pending_query"] = query
            user_sessions[user_id] = session
        
        # Double check translation with fallback if AI stayed in English
        # (AI sometimes defaults back to English if context is complex)
        final_response = from_english(answer, user_lang)
        
        return {"response": final_response, "language": user_lang, "audio": text_to_speech(final_response, user_lang)}

    except Exception as e:
        return {"error": str(e)}

@app.post("/ask")
def ask(request: AskRequest):
    answer = get_answer(request.question, user_lang=request.lang)
    return {"answer": answer}

if __name__ == "__main__":
    import uvicorn
    print("\nStarting VURA Unified Backend on http://127.0.0.1:5050 ...\n")
    uvicorn.run(app, host="127.0.0.1", port=5050)