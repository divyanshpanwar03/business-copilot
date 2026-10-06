from sentence_transformers import SentenceTransformer

from database import SessionLocal
from models import DocumentChunk


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def search_chunks(
    query: str,
    top_k: int = 5
):
    query_embedding = model.encode(
        query
    )

    db = SessionLocal()

    try:
        results = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.embedding.is_not(None)
            )
            .order_by(
                DocumentChunk.embedding.cosine_distance(
                    query_embedding.tolist()
                )
            )
            .limit(top_k)
            .all()
        )

        return results

    finally:
        db.close()