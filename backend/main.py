from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import faiss
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer
from huggingface_hub import InferenceClient

app = FastAPI(title="myScheme Copilot API")

# Add CORS so Frontend can communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    print("WARNING: HF_TOKEN environment variable not set. LLM features will fail.")

print("Loading Embedding Model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

print("Loading FAISS DB...")
db_path = os.environ.get("FAISS_INDEX_PATH", "schemes.index")
meta_path = os.environ.get("FAISS_META_PATH", "schemes_meta.json")

# In production (Render) these files will be packaged with the backend
if os.path.exists(db_path):
    index = faiss.read_index(db_path)
else:
    print(f"Index not found at {db_path}. RAG will fail.")

if os.path.exists(meta_path):
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta_data = json.load(f)
else:
    print(f"Meta data not found at {meta_path}. RAG will fail.")

# Hugging Face LLM - Using Mistral
# We can use mistralai/Mistral-7B-Instruct-v0.2 or meta-llama/Meta-Llama-3-8B-Instruct
llm_client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_TOKEN
)

class ChatRequest(BaseModel):
    query: str

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "myscheme-copilot"}

@app.post("/chat")
def chat(request: ChatRequest):
    query = request.query
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        # 1. Embed query
        query_vector = embedding_model.encode([query]).astype('float32')
        
        # 2. Vector Search (Top 3)
        k = 3
        distances, indices = index.search(query_vector, k)
        
        retrieved_contexts = []
        for idx in indices[0]:
            if idx < len(meta_data):
                retrieved_contexts.append(meta_data[idx]['text'])
                
        # 3. Assemble Prompt
        context_block = "\n\n---\n\n".join(retrieved_contexts)
        prompt = f"""<s>[INST] You are a highly helpful and expert AI assistant for Indian Government schemes (myScheme).
Use the provided retrieved context about government schemes to answer the user's question accurately.
If the answer is not contained in the context, politely inform the user that you don't have the specific details.
Provide completely readable, structured responses with bullets where necessary. 

### Context (Relevant Schemes):
{context_block}

### Question:
{query}
[/INST]"""

        # 4. Infer via Hugging Face API
        if not HF_TOKEN:
            return {"answer": "Error: HF_TOKEN is not configured for the backend.", "sources": retrieved_contexts}
            
        response = llm_client.text_generation(prompt, max_new_tokens=500, temperature=0.3, return_full_text=False)
        
        return {
            "answer": response.strip(),
            "sources": [meta_data[i]['name'] for i in indices[0] if i < len(meta_data)]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
