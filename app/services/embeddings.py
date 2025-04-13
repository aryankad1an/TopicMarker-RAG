from sentence_transformers import SentenceTransformer
from app.config import settings

_model = None

def get_embedding(text: str) -> list[float]:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.hf_embedding_model)
    return _model.encode(text).tolist()