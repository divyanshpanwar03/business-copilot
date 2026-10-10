import re

from sentence_transformers import SentenceTransformer
from sqlalchemy import func

from database import SessionLocal
from models import DocumentChunk


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

RRF_K = 60

model = None


STOP_WORDS = {
    "when", "does", "what", "is", "the",
    "a", "an", "for", "of", "to", "and",
    "in", "on", "how", "do", "which", "are",
    "was", "were", "be", "by"
}


def get_embedding_model():
    global model

    if model is None:
        model = SentenceTransformer(MODEL_NAME)

    return model


def build_keyword_query(query: str) -> str:
    """
    Convert the user question into a PostgreSQL
    full-text search query.
    """

    tokens = re.findall(
        r"[a-zA-Z0-9]+",
        query.lower()
    )

    # Expand common compliance acronyms.
    if "epf" in tokens:
        return "provident & fund"

    if "esi" in tokens or "esic" in tokens:
        return "state & insurance"

    # General fallback for other questions.
    terms = []

    for token in tokens:
        if token not in STOP_WORDS:
            terms.append(token)

    # Remove duplicates while preserving order.
    unique_terms = list(dict.fromkeys(terms))

    return " | ".join(unique_terms)


def search_chunks(
    query: str,
    top_k: int = 5,
    candidate_k: int = 20,
    mode: str = "vector"
):
    """
    Search document chunks using vector search,
    keyword search, or hybrid search.

    Modes:
        vector  -> semantic search only
        keyword -> PostgreSQL full-text search only
        hybrid  -> combine both rankings using RRF
    """

    if mode not in {"vector", "keyword", "hybrid"}:
        raise ValueError(
            "mode must be 'vector', 'keyword', or 'hybrid'"
        )

    use_vector = mode in {"vector", "hybrid"}
    use_keyword = mode in {"keyword", "hybrid"}

    # Generate the query embedding only when required.
    query_embedding = None

    if use_vector:
        query_embedding = get_embedding_model().encode(
            query
        ).tolist()

    keyword_query_text = ""

    if use_keyword:
        keyword_query_text = build_keyword_query(query)

    db = SessionLocal()

    try:
        vector_results = []
        keyword_results = []

        # =========================================
        # A. VECTOR SEARCH
        # =========================================

        if use_vector:

            distance_expression = (
                DocumentChunk.embedding.cosine_distance(
                    query_embedding
                )
            )

            vector_results = (
                db.query(
                    DocumentChunk,
                    distance_expression.label("distance")
                )
                .filter(
                    DocumentChunk.embedding.is_not(None)
                )
                .order_by(distance_expression)
                .limit(candidate_k)
                .all()
            )

        # =========================================
        # B. KEYWORD SEARCH
        # =========================================

        if use_keyword and keyword_query_text:

            document_vector = func.to_tsvector(
                "english",
                DocumentChunk.chunk_text
            )

            search_query = func.to_tsquery(
                "english",
                keyword_query_text
            )

            keyword_score_expression = func.ts_rank(
                document_vector,
                search_query
            )

            keyword_results = (
                db.query(
                    DocumentChunk,
                    keyword_score_expression.label(
                        "keyword_score"
                    )
                )
                .filter(
                    document_vector.op("@@")(search_query)
                )
                .order_by(
                    keyword_score_expression.desc()
                )
                .limit(candidate_k)
                .all()
            )

        # =========================================
        # C. VECTOR-ONLY RESULTS
        # =========================================

        if mode == "vector":

            results = []

            for rank, (chunk, distance) in enumerate(
                vector_results,
                start=1
            ):

                results.append({
                    "chunk": chunk,
                    "rrf_score": None,
                    "vector_distance": float(distance),
                    "vector_rank": rank,
                    "keyword_score": None,
                    "keyword_rank": None
                })

            return results[:top_k]

        # =========================================
        # D. KEYWORD-ONLY RESULTS
        # =========================================

        if mode == "keyword":

            results = []

            for rank, (chunk, keyword_score) in enumerate(
                keyword_results,
                start=1
            ):

                results.append({
                    "chunk": chunk,
                    "rrf_score": None,
                    "vector_distance": None,
                    "vector_rank": None,
                    "keyword_score": float(keyword_score),
                    "keyword_rank": rank
                })

            return results[:top_k]

        # =========================================
        # E. HYBRID SEARCH USING RRF
        # =========================================

        combined_results = {}

        # Add vector-search results.
        for rank, (chunk, distance) in enumerate(
            vector_results,
            start=1
        ):

            combined_results[chunk.id] = {
                "chunk": chunk,
                "rrf_score": 1 / (RRF_K + rank),
                "vector_distance": float(distance),
                "vector_rank": rank,
                "keyword_score": None,
                "keyword_rank": None
            }

        # Add keyword-search results.
        for rank, (chunk, keyword_score) in enumerate(
            keyword_results,
            start=1
        ):

            if chunk.id not in combined_results:

                combined_results[chunk.id] = {
                    "chunk": chunk,
                    "rrf_score": 0.0,
                    "vector_distance": None,
                    "vector_rank": None,
                    "keyword_score": float(keyword_score),
                    "keyword_rank": rank
                }

            else:

                combined_results[chunk.id][
                    "keyword_score"
                ] = float(keyword_score)

                combined_results[chunk.id][
                    "keyword_rank"
                ] = rank

            combined_results[chunk.id][
                "rrf_score"
            ] += 1 / (RRF_K + rank)

        # Sort by the combined ranking score.
        results = sorted(
            combined_results.values(),
            key=lambda item: item["rrf_score"],
            reverse=True
        )

        return results[:top_k]

    finally:
        db.close()