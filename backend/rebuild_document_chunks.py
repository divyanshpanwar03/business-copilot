import argparse
import hashlib
import sys
from pathlib import Path

# Handle special characters extracted from PDFs on Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(errors="replace")


from chunker import chunk_document
from database import SessionLocal
from models import DocumentChunk


# ============================================================
# 1. CONFIGURATION
# ============================================================

DOCUMENT_NAME = "Code on Social Security, 2020"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EXPECTED_EMBEDDING_DIMENSION = 384

BATCH_SIZE = 32


# ============================================================
# 2. GENERATE A CONTENT HASH
# ============================================================

def calculate_content_hash(text):
    """
    Create a SHA-256 hash of the chunk text.

    The hash helps us identify the content of a chunk.
    If the text changes, its hash will normally change too.
    """

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


# ============================================================
# 3. CREATE EMBEDDINGS
# ============================================================

def generate_embeddings(chunks):
    """
    Generate one embedding for each chunk.

    The same embedding model used by the existing retrieval
    system is retained to keep the embedding dimensions
    compatible with the pgvector column.
    """

    from sentence_transformers import SentenceTransformer

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print(
        f"\nLoading embedding model: {MODEL_NAME}",
        flush=True,
    )

    model = SentenceTransformer(MODEL_NAME)

    print(
        f"Generating embeddings for {len(texts)} chunks...",
        flush=True,
    )

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "The number of generated embeddings does not "
            "match the number of chunks."
        )

    if embeddings.shape[1] != EXPECTED_EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Expected {EXPECTED_EMBEDDING_DIMENSION}-dimensional "
            f"embeddings, but received {embeddings.shape[1]}."
        )

    return embeddings


# ============================================================
# 4. PREPARE DATABASE RECORDS
# ============================================================

def prepare_records(
    chunks,
    embeddings,
    document_name,
    source,
    authority,
):
    """
    Prepare SQLAlchemy DocumentChunk objects.

    Each record contains:
        - Document name
        - Source metadata
        - Authority
        - PDF page number
        - Chunk text
        - Content hash
        - Embedding vector
    """

    records = []

    for chunk, embedding in zip(chunks, embeddings):

        record = DocumentChunk(
            document_name=document_name,
            source=source,
            authority=authority,
            page_number=chunk["page_number"],
            section=None,
            chunk_text=chunk["text"],
            content_hash=calculate_content_hash(
                chunk["text"]
            ),
            embedding=embedding.tolist(),
        )

        records.append(record)

    return records


# ============================================================
# 5. MAIN REBUILD PROCESS
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Rebuild stored document chunks and embeddings "
            "using the updated chunker."
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Replace the existing chunks for the specified "
            "document. Without this flag, run a dry run only."
        ),
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # A. Generate new chunks.
        # ----------------------------------------------------

        print("\nREBUILD DOCUMENT CHUNKS")
        print("=" * 70)

        print(f"Document: {DOCUMENT_NAME}")

        print("\nGenerating chunks...")

        chunks = chunk_document()

        if not chunks:
            raise RuntimeError(
                "The chunker returned zero chunks. "
                "No database records were changed."
            )

        print(
            f"New chunks generated: {len(chunks)}"
        )

        # ----------------------------------------------------
        # B. Inspect existing records for this document.
        # ----------------------------------------------------

        existing_records = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_name == DOCUMENT_NAME
            )
            .all()
        )

        existing_count = len(existing_records)

        print(
            f"Existing chunks for this document: "
            f"{existing_count}"
        )

        if existing_records:

            # Preserve the existing source metadata.
            source = next(
                (
                    row.source
                    for row in existing_records
                    if row.source
                ),
                None,
            )

            # Preserve the existing authority metadata.
            authority = next(
                (
                    row.authority
                    for row in existing_records
                    if row.authority
                ),
                None,
            )

            document_name = existing_records[0].document_name

            if source is None:
                raise RuntimeError(
                    "Existing records do not contain source "
                    "metadata. Review the intended source before "
                    "replacing any records."
                )

            if authority is None:
                raise RuntimeError(
                    "Existing records do not contain authority "
                    "metadata. Review the intended authority before "
                    "replacing any records."
                )

        else:

            document_name = DOCUMENT_NAME

            source = None
            authority = None

        # ----------------------------------------------------
        # C. Dry-run mode.
        # ----------------------------------------------------

        if not args.apply:

            print("\nDRY RUN COMPLETED")

            print(
                "No database records were changed."
            )

            print(
                f"Document to replace: {DOCUMENT_NAME}"
            )

            print(
                f"Old chunks to replace: {existing_count}"
            )

            print(
                f"New chunks to insert: {len(chunks)}"
            )

            print(
                "\nAfter verifying your database backup, "
                "run this script with --apply to perform "
                "the replacement."
            )

            return

        # ----------------------------------------------------
        # D. Safety checks before replacement.
        # ----------------------------------------------------

        if existing_count == 0:
            raise RuntimeError(
                "No existing records were found for this exact "
                "document name. Replacement was cancelled to "
                "prevent accidental insertion under the wrong "
                "document identity."
            )

        if not source or not authority:
            raise RuntimeError(
                "Required source or authority metadata is missing. "
                "No database records were changed."
            )

        # ----------------------------------------------------
        # E. Generate every embedding BEFORE deleting old rows.
        # ----------------------------------------------------

        embeddings = generate_embeddings(chunks)

        new_records = prepare_records(
            chunks=chunks,
            embeddings=embeddings,
            document_name=document_name,
            source=source,
            authority=authority,
        )

        print(
            f"\nPrepared new records: {len(new_records)}"
        )

        # ----------------------------------------------------
        # F. Replace the records in one database transaction.
        # ----------------------------------------------------

        print(
            "\nReplacing old chunks for this document...",
            flush=True,
        )

        try:

            deleted_count = (
                db.query(DocumentChunk)
                .filter(
                    DocumentChunk.document_name == DOCUMENT_NAME
                )
                .delete(synchronize_session=False)
            )

            db.add_all(new_records)

            # Commit both deletion and insertion together.
            db.commit()

        except Exception:

            # If insertion or commit fails, undo the
            # uncommitted database changes.
            db.rollback()

            raise

        # ----------------------------------------------------
        # G. Verify the result.
        # ----------------------------------------------------

        final_count = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_name == DOCUMENT_NAME
            )
            .count()
        )

        print("\n" + "=" * 70)
        print("REBUILD COMPLETED")
        print("=" * 70)

        print(
            f"Old records deleted: {deleted_count}"
        )

        print(
            f"New records inserted: {len(new_records)}"
        )

        print(
            f"Records now stored for this document: "
            f"{final_count}"
        )

        if final_count != len(new_records):
            raise RuntimeError(
                "Verification failed: the number of stored "
                "records differs from the number inserted."
            )

        print(
            "\nOnly records matching this document name "
            "were replaced. Other documents were not targeted."
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()