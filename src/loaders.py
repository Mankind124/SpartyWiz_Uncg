from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document


def load_files(paths: Iterable[str | Path]) -> List[Document]:
    docs: List[Document] = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            for ext in ("*.pdf", "*.md"):
                for f in p.rglob(ext):
                    docs.extend(_load_file(f))
        elif p.exists():
            docs.extend(_load_file(p))
    return docs


def _load_file(path: Path) -> List[Document]:
    if path.suffix.lower() == ".pdf":
        loader = PyPDFLoader(str(path))
        return loader.load()
    if path.suffix.lower() == ".md":
        loader = UnstructuredMarkdownLoader(str(path))
        return loader.load()
    return []


def load_urls(urls: Optional[List[str]] = None) -> List[Document]:
    if not urls:
        return []
    # Respect USER_AGENT if provided; otherwise set a sensible default
    ua = os.getenv("USER_AGENT") or "SpartyWiz/1.0 (UNCG AI Innovation; https://www.uncg.edu)"
    loader = WebBaseLoader(web_paths=urls, header_template={"User-Agent": ua})
    docs = loader.load()
    # Clean HTML-heavy text a bit
    for d in docs:
        if 'text' in d.metadata:
            continue
        # Best-effort cleanup if HTML content present
        d.page_content = _clean_html(d.page_content)
    return docs


def _clean_html(text: str) -> str:
    soup = BeautifulSoup(text, 'html.parser')
    # Remove nav/aside/script/style
    for tag in soup(['nav', 'aside', 'script', 'style']):
        tag.decompose()
    return soup.get_text(" ").strip()
