from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain.chains.history_aware_retriever import (
    create_history_aware_retriever,
)
from langchain_core.prompts import MessagesPlaceholder

from .utils import ensure_dir, get_config
from .prompts import RAG_PROMPT, CONTEXTUALIZE_QUESTION_PROMPT


def build_vectorstore(docs: List[Document], vector_dir: str, embed_model: str,
                      chunk_size: int = 900, chunk_overlap: int = 120) -> FAISS:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name=embed_model)
    vs = FAISS.from_documents(chunks, embedding=embeddings)
    ensure_dir(vector_dir)
    vs.save_local(vector_dir)
    return vs


def load_vectorstore(vector_dir: str, embed_model: str) -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=embed_model)
    return FAISS.load_local(vector_dir, embeddings, allow_dangerous_deserialization=True)


def vectorstore_exists(vector_dir: str | Path) -> bool:
    """Return True if FAISS index files exist in the given directory."""
    p = Path(vector_dir)
    return (p / "index.faiss").exists() and (p / "index.pkl").exists()


def get_retriever(vector_dir: str, embed_model: str):
    vs = load_vectorstore(vector_dir, embed_model)
    return vs.as_retriever(search_kwargs={"k": 5})


def format_docs(docs: List[Document]) -> str:
    parts: List[str] = []
    for d in docs:
        meta = d.metadata or {}
        src = meta.get('source', '')
        title = meta.get('title', Path(src).stem if src else '')
        parts.append(f"[Source: {title}]\n{d.page_content}")
    return "\n\n".join(parts)


def _make_llm(model: str, temperature: float, api_key: str) -> ChatGroq:
    return ChatGroq(model=model, temperature=temperature, groq_api_key=api_key)


def build_rag_chain():
    cfg = get_config()
    # Build LLM list (primary + fallbacks) and let LangChain handle runtime fallback
    model_list = [m for m in [cfg['GROQ_MODEL'], *cfg.get('GROQ_FALLBACKS', [])] if m]
    if not model_list:
        raise RuntimeError("No Groq model configured. Set GROQ_MODEL in .env")
    llms = [_make_llm(m, cfg['TEMPERATURE'], cfg['GROQ_API_KEY']) for m in model_list]
    if len(llms) > 1:
        llm = llms[0].with_fallbacks(llms[1:])
    else:
        llm = llms[0]

    base_retriever = get_retriever(cfg['VECTOR_DIR'], cfg['EMBED_MODEL'])

    # History-aware retriever: turn follow-ups into standalone questions
    contextualize_prompt = PromptTemplate.from_template(CONTEXTUALIZE_QUESTION_PROMPT)
    hist_aware_retriever = create_history_aware_retriever(
        llm=llm,
        retriever=base_retriever,
        prompt=contextualize_prompt,
    )

    prompt = PromptTemplate.from_template(RAG_PROMPT)

    # The retriever expects a dict with keys {'input','chat_history'}
    to_retriever = RunnableLambda(lambda x: {"input": x.get("question", x), "chat_history": x.get("chat_history", "")})
    rag_chain = (
        {
            "context": to_retriever | hist_aware_retriever | format_docs,
            "question": RunnableLambda(lambda x: x.get("question", x)),
            "chat_history": RunnableLambda(lambda x: x.get("chat_history", "")),
            "profile": RunnableLambda(lambda x: x.get("profile", {})),
        }
        | prompt
        | llm
    )
    return rag_chain, hist_aware_retriever
