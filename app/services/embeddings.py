from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")  # 384-d

def get_embedding(text: str) -> list[float]:
    embedding = model.encode(text)
    # Pad to 1024-dim
    padded_embedding = embedding.tolist() + [0.0] * (1024 - len(embedding))
    return padded_embedding
