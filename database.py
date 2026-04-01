import os
import chromadb
from chromadb.utils import embedding_functions

# =========================
# ⚙️ CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "university_data"

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 150

# =========================
# ✂️ CHUNK FUNCTION
# =========================
def chunk_text(text):
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start = end - CHUNK_OVERLAP

    return chunks

# =========================
# 🚀 BUILD DATABASE
# =========================
def build_chroma():
    print("🚀 Building NEW Chroma DB (chunk=1000)...")

    # delete old DB
    if os.path.exists(CHROMA_DB_DIR):
        import shutil
        shutil.rmtree(CHROMA_DB_DIR)
        print("🗑️ Old DB deleted")

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

    embedding_func = embedding_functions.DefaultEmbeddingFunction()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_func
    )

    documents = []
    metadatas = []
    ids = []

    total_chunks = 0

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".txt"):

            path = os.path.join(DATA_DIR, filename)
            print(f"📄 Processing {filename}")

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = chunk_text(content)

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": filename,
                    "chunk": i
                })
                ids.append(f"{filename}_{i}")
                total_chunks += 1

    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        print(f"✅ Stored {total_chunks} chunks")
    else:
        print("❌ No TXT files found")

# =========================
# ▶️ RUN
# =========================
if __name__ == "__main__":
    build_chroma()