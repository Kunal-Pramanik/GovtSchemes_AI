# GovtSchemes_AI

## 1️⃣ Final System Architecture
```
User (Browser Chat UI)
        │
        ▼
Frontend (Vercel - Next.js / React)
        │
        ▼
Backend API (Render - FastAPI)
        │
        ├── Vector Search (Hugging Face dataset / FAISS)
        │
        └── LLM (Open-source model or API)
                │
                ▼
           Generated Answer
```

### Flow:

```
User question
      ↓
API receives query
      ↓
Embedding generation
      ↓
Vector search
      ↓
Top scheme documents retrieved
      ↓
LLM generates answer
      ↓
Response returned to UI

```
## 2️⃣ Knowledge Base Preparation
```
myscheme_cleaned.csv
combined_text column
```

## 3️⃣ Vectorization (Hugging Face)

Use sentence embeddings.

Recommended model:
```bash
sentence-transformers/all-MiniLM-L6-v2
```

Store embeddings.

Options:
```
Option A: FAISS index
Option B: Hugging Face dataset
```
Upload to Hugging Face dataset repository.

## 4️⃣ Retrieval System

Use FAISS.

## 5️⃣ LLM Layer

The LLM generates the final answer.

You can use:

### Open-source LLM via Hugging Face:

- Mistral 7B
- Llama 3

### Prompt template
 ```
You are a helpful assistant for government schemes.

Context:
{retrieved_scheme_data}

User question:
{question}

Provide a clear answer explaining eligibility,
benefits, and application process if available.
```

## 6️⃣ Backend API (Render)

Use FastAPI.

Deploy to Render.

Result:
```
https://scheme-copilot-api.onrender.com/chat
```

## 7️⃣ Frontend (Vercel)

Build a simple chat interface.

Framework:

Next.js

UI layout:
```
--------------------------------
SchemeCopilot AI
--------------------------------
User: I am a student, what schemes exist?

AI:
Here are schemes available for students...
--------------------------------

```

## 8️⃣ Final Deployment Architecture

```
Frontend
(Vercel)
scheme-copilot.vercel.app
        │
        ▼
Backend API
(Render)
scheme-copilot-api.onrender.com
        │
        ▼
Vector Database
(Hugging Face / FAISS)
        │
        ▼
LLM
(Hugging Face model)
```

