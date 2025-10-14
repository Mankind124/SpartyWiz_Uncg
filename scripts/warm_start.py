"""
Warm-start utility to pre-download embedding models to avoid first-run latency.
"""
from sentence_transformers import SentenceTransformer


def main():
    model_name = 'sentence-transformers/all-MiniLM-L6-v2'
    print(f"Downloading embeddings model: {model_name} …")
    _ = SentenceTransformer(model_name)
    print("Done.")


if __name__ == "__main__":
    main()
