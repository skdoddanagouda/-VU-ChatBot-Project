import chromadb
from google import genai
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =========================
# ⚙️ CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "university_data"
CHROMA_ENABLED = True  # Global flag

# Global Chroma Client
try:
    CHROMA_CLIENT = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    # Check if collection exists
    collections = CHROMA_CLIENT.list_collections()
    collection_names = [c.name for c in collections]
    
    if COLLECTION_NAME in collection_names:
        CHROMA_COLLECTION = CHROMA_CLIENT.get_collection(name=COLLECTION_NAME)
        count = CHROMA_COLLECTION.count()
        print(f"[OK] ChromaDB collection '{COLLECTION_NAME}' loaded with {count} documents.")
    else:
        print(f"[WARNING] ChromaDB collection '{COLLECTION_NAME}' NOT found. Falling back to keyword search.")
        CHROMA_COLLECTION = None
        CHROMA_ENABLED = False
except Exception as e:
    print(f"[WARNING] ChromaDB error: {e}. Defaulting to keyword search.")
    CHROMA_COLLECTION = None
    CHROMA_ENABLED = False

# Summary of knowledge base files
try:
    DATA_DIR = os.path.join(BASE_DIR, "data")
    if os.path.exists(DATA_DIR):
        files = [f for f in os.listdir(DATA_DIR) if f.endswith(".txt")]
        print(f"[INFO] Found {len(files)} knowledge base files (.txt) in {DATA_DIR}")
    else:
        print(f"[WARNING] Knowledge base directory NOT found: {DATA_DIR}")
except Exception as e:
    print(f"[ERROR] Error scanning data directory: {e}")

# 🔐 API Key Configuration
api_key = os.getenv("GGEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[ERROR] No GEMINI_API_KEY found in environment variables.")
client_ai = genai.Client(api_key=api_key)

# =========================
# 🔤 QUERY CLEANING
# =========================
def normalize_query(query):
    query = query.lower().strip()

    corrections = {
        "attendence": "attendance",
        "attence": "attendance",
        "attendace": "attendance",
        "techer": "teacher",
        "timetabel": "timetable",
        "timetablee": "timetable",
        "univesity": "university",
        "vidyashilp": "vidyashilp"
    }

    for wrong, correct in corrections.items():
        query = query.replace(wrong, correct)

    return query


# =========================
# 🔍 FALLBACK: KEYWORD SEARCH
# =========================
def keywords_fallback(query, k=3):
    """Simple keyword search across text files if Chroma fails."""
    try:
        DATA_DIR = os.path.join(BASE_DIR, "data")
        if not os.path.exists(DATA_DIR):
             # Try root data if not in backend/data
            DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
            if not os.path.exists(DATA_DIR):
                return []

        # Find all txt files
        files = [f for f in os.listdir(DATA_DIR) if f.endswith(".txt")]
        keywords = [w for w in query.lower().split() if len(w) > 3]
        
        matches = []
        for filename in files:
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                score = sum(1 for kw in keywords if kw in content.lower())
                if score > 0:
                    matches.append((score, content[:1500])) # Get first 1500 chars

        # Sort by score and return top k
        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches[:k]]
    except Exception as e:
        print(f"Fallback Error: {e}")
        return []


# =========================
# 🔍 RETRIEVE FROM CHROMA
# =========================
def retrieve_chunks(query, k=5):
    global CHROMA_ENABLED
    if not CHROMA_ENABLED or not CHROMA_COLLECTION:
        return keywords_fallback(query)

    try:
        results = CHROMA_COLLECTION.query(
            query_texts=[query],
            n_results=k
        )
        docs = results.get("documents", [[]])[0]
        if not docs:
            return keywords_fallback(query)
        return docs
    except Exception as e:
        print(f"Retrieval Error: {e}. Switching to keyword search permanently.")
        CHROMA_ENABLED = False # Disable for the rest of the session
        return keywords_fallback(query)


# =========================
# 🤖 ANSWER GENERATION
# =========================
def get_answer(query, user_lang="en"):
    query = normalize_query(query)
    docs = retrieve_chunks(query)

    if not docs:
        return "I couldn't find accurate information in our database. Please provide your email, and your query will be answered soon by our team."

    context = "\n\n".join([
        f"Chunk {i+1}:\n{doc}" for i, doc in enumerate(docs)
    ])

    prompt = f"""
You are VURA, the official AI assistant for Vidyashilp University, Bengaluru.

Follow this STRICT 5-step framework when answering:
Respond in this language: {user_lang}

1. UNDERSTAND THE QUESTION  
Carefully understand what the user is asking.
Respond strictly in this language: {user_lang}.
Use the NATIVE SCRIPT of the language (e.g., Devanagari for Hindi, Bengali script for Bengali).
Do NOT use Romanized text or English unless specifically asked.
Answer ONLY using the information given in the context below.  
Do NOT use outside knowledge or assumptions.
Carefully read ALL chunks.

If events or any data are mentioned in ANY chunk, list them clearly.
Do NOT miss information.

3. EXTRACT RELEVANT INFORMATION  
Identify the most relevant parts of the context and ignore unrelated sections.

4. FORM A CLEAR AND COMPLETE ANSWER  
- Always give a COMPLETE answer, not partial  
- Combine information from multiple parts of the context if needed  
- Write in full, natural sentences like a website or official document  

5. HANDLE MISSING INFORMATION  
- If NO relevant info exists → say:  
  "I couldn't find accurate information. Please provide your mail, your query will be answered soon."

6. Give a DETAILED answer covering ALL relevant points.
- Answer should be at least 5-6 sentences if information is available.

----------------------------------------
CONTEXT:
{context}

----------------------------------------
QUESTION:
{query}

----------------------------------------
STRICT LANGUAGE RULE: 
You MUST respond strictly in the following language: {user_lang}.
You MUST use the NATIVE SCRIPT of that language (e.g. Devanagari script for Hindi, Tamil script for Tamil).
Do NOT use English or Romanized text.

ANSWER:
"""

    for attempt in range(3):
        try:
            response = client_ai.models.generate_content(
                model="gemini-flash-latest", 
                contents=prompt
            )
            return response.text.strip() if response.text else "No response generated."

        except Exception as e:
            print(f"Attempt {attempt+1} failed:", str(e))
            time.sleep(2)

    return "The AI service is currently busy. Please try your question again in a moment."


# =========================
# 🌍 AI LANGUAGE DETECTION
# =========================
def detect_language_ai(text):
    """Detects the ISO 639-1 language code of the given text using AI."""
    if not text or len(text.strip()) < 1:
        return "en"
    
    prompt = f"""
    Analyze the following text and return ONLY the ISO 639-1 language code (e.g., 'hi', 'ta', 'en', 'bn').
    If the text is in an Indian language, be very specific.
    Text: "{text}"
    Code:
    """
    try:
        response = client_ai.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        code = response.text.strip().lower()
        # Basic cleanup in case of extra words
        if len(code) > 5:
            code = code[:2]
        return code if code else "en"
    except Exception as e:
        print(f"AI Detection error: {e}")
        return "en"

# =========================
# ▶️ MAIN (CLI MODE ONLY)
# =========================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        print("\nRAG SYSTEM READY (CLI MODE)\n")
        while True:
            query = input("Ask something (type 'exit' to quit): ")
            if query.lower() == "exit":
                break
            print("\n🤖 Answer:\n", get_answer(query), "\n" + "="*50)
    else:
        print("\n[INFO] RAG module loaded. Use main.py to start the unified server.\n")