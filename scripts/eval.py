from __future__ import annotations

from src.eval_rag import QAExample, simple_precision
from src.rag_pipeline import build_rag_chain


def main():
    chain, retriever = build_rag_chain()
    eval_pairs = [
        QAExample(
            question="How do I contact financial aid?",
            expected="financial aid",  # keyword expected in retrieved context
        ),
        QAExample(
            question="Where do I find registrar deadlines?",
            expected="registrar",
        ),
    ]
    report = simple_precision(eval_pairs, retriever, top_k=5)
    print(report)


if __name__ == "__main__":
    main()
