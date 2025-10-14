from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from src.loaders import load_files, load_urls
from src.rag_pipeline import build_vectorstore
from src.utils import get_config


def main():
    parser = argparse.ArgumentParser(description="Ingest files/urls into FAISS vector store")
    parser.add_argument("--paths", nargs="*", default=["data"], help="Files or folders to ingest")
    parser.add_argument("--urls", nargs="*", default=[], help="Web URLs to crawl (single hop)")
    args = parser.parse_args()

    cfg = get_config()

    file_docs = load_files(args.paths)
    url_docs = load_urls(args.urls)
    docs = file_docs + url_docs

    if not docs:
        print("No documents found. Add PDFs/MDs in data/ or pass --urls.")
        return

    build_vectorstore(
        docs,
        vector_dir=cfg['VECTOR_DIR'],
        embed_model=cfg['EMBED_MODEL'],
        chunk_size=cfg['CHUNK_SIZE'],
        chunk_overlap=cfg['CHUNK_OVERLAP'],
    )
    print(f"Indexed {len(docs)} documents into {cfg['VECTOR_DIR']}")


if __name__ == "__main__":
    main()
