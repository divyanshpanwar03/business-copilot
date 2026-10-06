import hashlib

from sentence_transformers import SentenceTransformer

from database import SessionLocal
from models import DocumentChunk
from chunker import load_chunks


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

DOCUMENT_NAME = "Code on Social Security, 2020"
SOURCE = "Ministry of Labour and Employment"
AUTHORITY = "Ministry of Labour and Employment"


def generate_hash(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


model = SentenceTransformer(MODEL_NAME)

chunks = load_chunks()

db = SessionLocal()

try:
    new_count = 0
    embedded_count = 0
    skipped_count = 0

    for chunk in chunks:

        content_hash = generate_hash(
            chunk["text"]
        )

        existing_chunk = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_name
                == DOCUMENT_NAME,
                DocumentChunk.page_number
                == chunk["page_number"],
                DocumentChunk.content_hash
                == content_hash
            )
            .first()
        )

        if existing_chunk:

            if existing_chunk.embedding is not None:
                skipped_count += 1
                continue

            embedding = model.encode(
                chunk["text"]
            )

            existing_chunk.embedding = (
                embedding.tolist()
            )

            embedded_count += 1
            continue

        embedding = model.encode(
            chunk["text"]
        )

        document_chunk = DocumentChunk(
            document_name=DOCUMENT_NAME,
            source=SOURCE,
            authority=AUTHORITY,
            page_number=chunk["page_number"],
            section=None,
            chunk_text=chunk["text"],
            content_hash=content_hash,
            embedding=embedding.tolist()
        )

        db.add(document_chunk)

        new_count += 1
        embedded_count += 1

    db.commit()

    print(f"New chunks: {new_count}")
    print(f"Embeddings created: {embedded_count}")
    print(f"Chunks skipped: {skipped_count}")

finally:
    db.close()