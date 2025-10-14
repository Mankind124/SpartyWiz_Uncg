from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from langchain_core.documents import Document


@dataclass
class QAExample:
    question: str
    expected: str


def simple_precision(eval_pairs: List[QAExample], retriever, top_k: int = 5) -> Dict:
    total = len(eval_pairs)
    hits = 0
    for ex in eval_pairs:
        docs: List[Document] = retriever.get_relevant_documents(ex.question)[:top_k]
        context = "\n".join(d.page_content for d in docs)
        if ex.expected.lower() in context.lower():
            hits += 1
    return {"n": total, "hits": hits, "precision@k": hits / total if total else 0.0}
