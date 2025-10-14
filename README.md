# SpartyWiz (UNCG) — RAG Chatbot with LangChain + Groq + Streamlit

SpartyWiz is an AI-powered campus assistant for UNC Greensboro. It uses Retrieval-Augmented Generation (RAG) to answer questions using official UNCG resources.

- LLM: Groq (fast inference)
- Orchestration: LangChain
- Embeddings: `sentence-transformers` via `HuggingFaceEmbeddings`
- Vector store: FAISS (local)
- UI: Streamlit
- Eval: RAGAS (optional) and simple precision-style checks

## Features
- Document ingestion from PDFs, URLs, and Markdown.
- Chunking + FAISS vector indexing with local cache.
- Configurable Groq model and temperature.
- Streamlit chat with sources, follow-ups, and feedback.
- Basic safety guardrails and prompt templates tailored to UNCG.

## Quickstart

1) Create and activate a Python 3.10+ environment.

2) Install dependencies:

```cmd
pip install -r requirements.txt
```

3) Set environment variables (create a `.env` file or set in your shell):

```
GROQ_API_KEY=your_key_here
# Optional overrides
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
GROQ_MODEL=llama-3.1-70b-versatile
```

4) Ingest data (place PDFs/MD/HTML in `data/` or pass URLs):

```cmd
python scripts/ingest.py --paths data --urls https://www.uncg.edu/ https://reg.uncg.edu/
```

5) Run Streamlit app:

```cmd
streamlit run app.py
```

6) Ask questions like:
- "What are the key registration deadlines this semester?"
- "How do I contact financial aid?"
- "What housing options exist for graduate students?"

## Project Structure
```
AI_Innovation/
├─ app.py                  # Streamlit UI
├─ src/
│  ├─ rag_pipeline.py      # Build retriever & chain
│  ├─ loaders.py           # File/URL loaders
│  ├─ prompts.py           # System & RAG prompts
│  ├─ utils.py             # Helpers: caching, env, etc
│  └─ eval_rag.py          # Basic evaluation harness
├─ scripts/
│  ├─ ingest.py            # CLI to create/update FAISS index
│  └─ warm_start.py        # Optional: pre-download models
├─ data/                   # Put PDFs/MD/HTML here
├─ .github/workflows/
│  └─ streamlit-deploy.yml # CI to validate build
├─ requirements.txt
├─ .env.example
├─ .gitignore
└─ README.md
```

## GitHub Deployment Notes
This repo is designed for:
- Local run with Streamlit
- Optional GitHub Actions checks (lint + smoke run)

For cloud deployment, you can:
- Use Streamlit Community Cloud and set `GROQ_API_KEY` in app secrets.
- Or deploy on Azure Web App/Render/Heroku with `pip install -r requirements.txt` and `streamlit run app.py`.

## Data Responsibility
Only ingest official, public UNCG documents/URLs or content you have rights to use. Verify outputs for accuracy. Include citations shown as sources in the UI.

## License
MIT
