import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def load_env(dotenv_path: Optional[str] = None):
    if dotenv_path is None:
        dotenv_path = Path('.') / '.env'
    load_dotenv(dotenv_path=dotenv_path, override=False)


def get_env(name: str, default: Optional[str] = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    if isinstance(val, str):
        v = val.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            return v[1:-1]
        return v
    return val


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_config():
    load_env()
    return {
        'GROQ_API_KEY': get_env('GROQ_API_KEY', ''),
        # Default to a widely-available Groq model; can be overridden via .env
        'GROQ_MODEL': os.getenv('GROQ_MODEL', 'llama3-70b-8192'),
        'EMBED_MODEL': os.getenv('EMBED_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
        'VECTOR_DIR': os.getenv('VECTOR_DIR', 'faiss_index'),
        'CHUNK_SIZE': int(os.getenv('CHUNK_SIZE', '900')),
        'CHUNK_OVERLAP': int(os.getenv('CHUNK_OVERLAP', '120')),
        'TEMPERATURE': float(os.getenv('TEMPERATURE', '0.2')),
        # Comma-separated fallback list for Groq models
        'GROQ_FALLBACKS': [m.strip() for m in os.getenv(
            'GROQ_FALLBACKS', 'llama3-70b-8192,mixtral-8x7b-32768,llama-3.1-8b-instant'
        ).split(',') if m.strip()],
    }
