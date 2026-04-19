from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import faiss
import numpy as np
import json
import os


from huggingface_hub import InferenceClient, hf_hub_download

# ---------------------------------------
# FastAPI App
# ---------------------------------------

app = FastAPI(title="GovtScheme_AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------
# Environment variables
# ---------------------------------------

HF_TOKEN = os.environ.get("HF_TOKEN")

if not HF_TOKEN:
    print("WARNING: HF_TOKEN not set. LLM inference will fail.")

# ---------------------------------------
# Load embedding model
# ---------------------------------------

print("Loading embedding model...")

embedding_client = InferenceClient(
    model="sentence-transformers/all-MiniLM-L6-v2",
    token=HF_TOKEN
)

print("Embedding model loaded.")

# ---------------------------------------
# Download FAISS index from Hugging Face
# ---------------------------------------

print("Downloading vector database from Hugging Face...")

try:
    index_path = hf_hub_download(
        repo_id="pramanikkunal65/GovtScheme_AI",
        filename="schemes.index",
        repo_type="dataset"
    )

    meta_path = hf_hub_download(
        repo_id="pramanikkunal65/GovtScheme_AI",
        filename="schemes_meta.json",
        repo_type="dataset"
    )

except Exception as e:
    print("Failed to download FAISS data:", e)
    raise

# ---------------------------------------
# Load FAISS index
# ---------------------------------------

print("Loading FAISS index...")

index = faiss.read_index(index_path)

with open(meta_path, "r", encoding="utf-8") as f:
    meta_data = json.load(f)

print(f"FAISS index loaded with {index.ntotal} vectors")

# ---------------------------------------
# Hugging Face LLM client
# ---------------------------------------

llm_client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_TOKEN
)

# ---------------------------------------
# Request schema
# ---------------------------------------

class ChatRequest(BaseModel):
    query: str

# ---------------------------------------
# Health check
# ---------------------------------------

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "myscheme-copilot"
    }

# ---------------------------------------
# Chat endpoint
# ---------------------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    try:

        # -----------------------------------
        # Step 1: Create embedding
        # -----------------------------------

        query_vector = np.array(embedding_client.feature_extraction(query),dtype="float32").reshape(1, -1)

        # -----------------------------------
        # Step 2: Vector search
        # -----------------------------------

        k = 3

        distances, indices = index.search(query_vector, k)

        retrieved_contexts = []

        for idx in indices[0]:
            if idx < len(meta_data):
                retrieved_contexts.append(meta_data[idx]["text"])

        # -----------------------------------
        # Step 3: Build prompt
        # -----------------------------------

        context_block = "\n\n---\n\n".join(retrieved_contexts)

        prompt = f"""
<s>[INST]
You are a highly helpful AI assistant for Indian Government welfare schemes.

Use the provided context to answer the user's question accurately.

If the answer is not available in the context, politely say that the information is not available.

Provide clear, readable responses with bullet points when appropriate.

### Context
{context_block}

### Question
{query}
[/INST]
"""

        # -----------------------------------
        # Step 4: LLM inference
        # -----------------------------------

        if not HF_TOKEN:
            return {
                "answer": "HF_TOKEN not configured on backend.",
                "sources": retrieved_contexts
            }

        response = llm_client.text_generation(
            prompt,
            max_new_tokens=400,
            temperature=0.3,
            return_full_text=False
        )

        # -----------------------------------
        # Step 5: Return response
        # -----------------------------------

        return {
            "answer": response.strip(),
            "sources": [
                meta_data[i]["name"]
                for i in indices[0]
                if i < len(meta_data)
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
