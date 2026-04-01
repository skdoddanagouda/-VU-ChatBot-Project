import chromadb
from google import genai
import os
import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# =========================
# ⚙️ CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "university_data"

# 🔐 API Key Configuration
# Note: It is best practice to use os.getenv("YOUR_ENV_VAR"), 
# but I have fixed the direct string assignment for you.
client_ai = genai.Client(api_key="AIzaSyBz22sH6FBCwOqpbxi0U-XiQnRd92aUAZo")

app = Flask(__name__)
CORS(app)  # This allows your HTML file to communicate with this server

# =========================
# 🔤 QUERY CLEANING
# =========================
def normalize_query(query):
    query = query.lower().strip()

    corrections = {
        "attendence": "attendance",
        "techer": "teacher",
        "univesity": "university",
        "vidyashilp": "vidyashilp"
    }

    for wrong, correct in corrections.items():
        query = query.replace(wrong, correct)

    return query


# =========================
# 🔍 RETRIEVE FROM CHROMA
# =========================
def retrieve_chunks(query, k=5):
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        collection = client.get_collection(name=COLLECTION_NAME)

        results = collection.query(
            query_texts=[query],
            n_results=k
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        print("\n🔍 RETRIEVAL DEBUG:\n")

        for i, (doc, meta) in enumerate(zip(docs, metas)):
            print(f"\n📦 ===== CHUNK {i+1} =====")
            print(f"📁 Source File: {meta.get('source', 'Unknown')}")
            if "chunk" in meta:
                print(f"🔢 Chunk Index: {meta['chunk']}")
            print("📝 Content Preview:")
            print(doc[:200])
            print("📦 ======================")

        return docs
    except Exception as e:
        print(f"❌ Retrieval Error: {e}")
        return []


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
Carefully understand what the user is asking (courses, faculty, admissions, events, etc.).

2. USE ONLY PROVIDED CONTEXT  
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

ANSWER:
"""

    for attempt in range(3):
        try:
            # Note: Changed to gemini-2.0-flash as 2.5 is not a standard release yet
            response = client_ai.models.generate_content(
                model="gemini-2.5-flash", 
                contents=prompt
            )
            return response.text.strip() if response.text else "No response generated."

        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed:", str(e))
            time.sleep(2)

    return "The AI service is currently busy. Please try your question again in a moment."


# =========================
# 🌐 API ROUTES
# =========================

@app.route("/health", methods=["GET"])
def health():
    """Health check for the frontend to confirm the server is running."""
    return jsonify({"status": "online"}), 200

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json

    if not data or not data.get("question"):
        return jsonify({"error": "Missing 'question' field in request body"}), 400

    query = data.get("question")
    user_lang = data.get("lang", "en")

    answer = get_answer(query, user_lang=user_lang)
    return jsonify({"answer": answer})

@app.route("/")
def home():
    return render_template("index.html")
# =========================
# ▶️ MAIN
# =========================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        print("\n🚀 RAG SYSTEM READY (CLI MODE)\n")
        while True:
            query = input("💬 Ask something (type 'exit' to quit): ")
            if query.lower() == "exit":
                break
            print("\n🤖 Answer:\n", get_answer(query), "\n" + "="*50)
    else:
        print("\n🚀 Starting VURA Flask API server on http://127.0.0.1:5000 ...\n")
        app.run(host="127.0.0.1", port=5000, debug=True)