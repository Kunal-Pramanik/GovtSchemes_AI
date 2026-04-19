from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import faiss
import numpy as np
import json
import os

from huggingface_hub import InferenceClient, hf_hub_download

# ---------------------------------------------------
# FastAPI App
# ---------------------------------------------------

app = FastAPI(title="GovtScheme_AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# Environment variables
# ---------------------------------------------------

HF_TOKEN = os.environ.get("HF_TOKEN")

if not HF_TOKEN:
    print("WARNING: HF_TOKEN not set. LLM and embeddings may fail.")

# ---------------------------------------------------
# Hugging Face Clients
# ---------------------------------------------------

print("Initializing Hugging Face clients...")

embedding_client = InferenceClient(
    model="sentence-transformers/all-MiniLM-L6-v2",
    token=HF_TOKEN
)

llm_client = InferenceClient(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    token=HF_TOKEN
)

print("HF clients initialized.")
# ---------------------------------------------------
# Download FAISS database
# ---------------------------------------------------

print("Downloading FAISS vector database...")

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

# ---------------------------------------------------
# Load FAISS
# ---------------------------------------------------

print("Loading FAISS index...")

index = faiss.read_index(index_path)

with open(meta_path, "r", encoding="utf-8") as f:
    meta_data = json.load(f)

print(f"FAISS index loaded with {index.ntotal} vectors")

# ---------------------------------------------------
# Request schema
# ---------------------------------------------------

class ChatRequest(BaseModel):
    query: str

# ---------------------------------------------------
# Health Check
# ---------------------------------------------------

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "GovtScheme_AI",
        "vectors_loaded": index.ntotal
    }

# ---------------------------------------------------
# Chat Endpoint
# ---------------------------------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    query = request.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:

        # Step 1 — Embedding
        query_vector = np.array(
            embedding_client.feature_extraction(query),
            dtype="float32"
        ).reshape(1, -1)

        # Step 2 — Vector Search
        k = 3
        distances, indices = index.search(query_vector, k)

        retrieved_contexts = []
        retrieved_ids = []

        for idx in indices[0]:
            if idx != -1 and idx < len(meta_data):
                retrieved_contexts.append(meta_data[idx]["text"])
                retrieved_ids.append(idx)

        # Step 3 — Prepare Context
        context_block = "\n\n---\n\n".join(retrieved_contexts)

        if not context_block:
            context_block = "No relevant scheme information found."

        # Step 4 — Prompt
        prompt = f"""
You are an expert AI assistant for Indian Government welfare schemes.

Answer the user's question using ONLY the provided scheme information.

If the information is not available, say that clearly.

Provide clean, readable answers with bullet points.

SCHEME DATA:
{context_block}

USER QUESTION:
{query}
"""

        # Step 5 — LLM Inference
        response = llm_client.chat_completion(
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )

        response_text = response.choices[0].message.content

        # Step 6 — Return Result
        return {
            "answer": response_text.strip(),
            "sources": [
                {
                    "scheme": meta_data[i]["name"],
                    "snippet": meta_data[i]["text"][:200]
                }
                for i in retrieved_ids
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
