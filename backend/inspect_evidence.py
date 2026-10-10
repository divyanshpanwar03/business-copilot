import sys

# Avoid Windows console encoding errors when displaying PDF text.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(errors="replace")


from database import SessionLocal
from models import DocumentChunk


# ============================================================
# 1. PASSAGES WE WANT TO VERIFY
# ============================================================

EVIDENCE_CASES = [
    {
        "question": "How does the Code define an inter-State migrant worker?",
        "expected_terms": [
            "inter-state migrant worker",
            "recruited directly by the employer or indirectly through contractor",
            "destination state",
        ],
    },
    {
        "question": "Which activities are included in the definition of a manufacturing process?",
        "expected_terms": [
            "manufacturing process",
            "making, altering, repairing",
            "pumping oil, water, sewage",
            "preserving or storing any article in cold storage",
        ],
    },
    {
        "question": "How much continuous service is generally required for gratuity?",
        "expected_terms": [
            "gratuity shall be payable to an employee",
            "continuous service for not less than five years",
        ],
    },
    {
        "question": "When is completion of five years of continuous service not necessary for gratuity?",
        "expected_terms": [
            "completion of continuous service of five years shall not be necessary",
            "expiration of fixed term employment",
        ],
    },
    {
        "question": "What special service-duration provision applies to working journalists?",
        "expected_terms": [
            "working journalist",
            '"five years" occurring in this sub-section shall be deemed to be three years',
        ],
    },
    {
        "question": "When does EPF coverage apply?",
        "expected_terms": [
            "employees' provident fund",
            "twenty or more employees",
        ],
    },
    {
        "question": "When does ESI coverage apply?",
        "expected_terms": [
            "employees' state insurance corporation",
            "ten or more persons",
        ],
    },
]


# ============================================================
# 2. NORMALIZE TEXT
# ============================================================

def normalize_text(text):
    """
    Make text easier to compare with expected phrases.

    This handles:
    - Uppercase and lowercase differences
    - Curly and straight quotation marks
    - Line breaks
    - Multiple spaces and tabs
    """

    text = str(text).casefold()

    text = (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )

    return " ".join(text.split())


# ============================================================
# 3. SEARCH STORED CHUNKS
# ============================================================

def inspect_case(rows, case):

    question = case["question"]

    expected_terms = case["expected_terms"]

    normalized_terms = [
        normalize_text(term)
        for term in expected_terms
    ]

    print("\n" + "=" * 85)
    print(f"QUESTION: {question}")
    print("=" * 85)

    matching_rows = []

    # Search the normalized text in Python rather than using
    # a literal PostgreSQL ILIKE pattern. This allows phrases
    # to match even when the original PDF contains line breaks.

    for row in rows:

        original_text = row.chunk_text or ""

        normalized_chunk = normalize_text(original_text)

        matched_terms = []
        missing_terms = []

        for original_term, normalized_term in zip(
            expected_terms,
            normalized_terms,
        ):

            if normalized_term in normalized_chunk:
                matched_terms.append(original_term)
            else:
                missing_terms.append(original_term)

        # Only display chunks containing at least one
        # of the expected phrases.
        if matched_terms:

            matching_rows.append(
                {
                    "row": row,
                    "text": normalized_chunk,
                    "matched_terms": matched_terms,
                    "missing_terms": missing_terms,
                }
            )

    # Show chunks containing the greatest number of expected
    # phrases first.
    matching_rows.sort(
        key=lambda item: (
            -len(item["matched_terms"]),
            item["row"].page_number
            if item["row"].page_number is not None
            else 0,
            item["row"].id,
        )
    )

    print(
        f"\nExpected phrases: {len(expected_terms)}"
    )

    print(
        f"Chunks containing at least one expected phrase: "
        f"{len(matching_rows)}"
    )

    if not matching_rows:

        print(
            "\nNo stored chunk contains any of the expected phrases."
        )

        return

    # Show up to five candidate chunks.
    for item in matching_rows[:5]:

        row = item["row"]

        text = item["text"]

        matched_terms = item["matched_terms"]

        missing_terms = item["missing_terms"]

        print("\n" + "-" * 85)

        print(f"Chunk ID: {row.id}")

        print(f"Document: {row.document_name}")

        print(f"Page metadata: {row.page_number}")

        print(
            f"Chunk length: {len(row.chunk_text or '')} characters"
        )

        print(
            f"Expected phrases found: "
            f"{len(matched_terms)}/{len(expected_terms)}"
        )

        print(f"Matched phrases: {matched_terms}")

        if missing_terms:
            print(f"Missing phrases: {missing_terms}")
        else:
            print(
                "VERIFICATION: All expected phrases "
                "exist in this stored chunk."
            )

        # Display text around the first matching phrase.
        # This avoids hiding relevant text later in the chunk.
        first_term = normalize_text(matched_terms[0])

        position = text.find(first_term)

        start = max(0, position - 200)

        end = min(
            len(text),
            position + len(first_term) + 600,
        )

        print("\nRelevant text excerpt:")

        print(text[start:end])


# ============================================================
# 4. MAIN PROGRAM
# ============================================================

def main():

    db = SessionLocal()

    try:

        print("\nINSPECTING STORED DOCUMENT EVIDENCE")

        print("=" * 85)

        # Load the stored chunks once, then inspect them locally.
        rows = (
            db.query(DocumentChunk)
            .order_by(
                DocumentChunk.page_number,
                DocumentChunk.id,
            )
            .all()
        )

        print(
            f"Total stored chunks inspected: {len(rows)}"
        )

        for case in EVIDENCE_CASES:

            inspect_case(rows, case)

        print("\n" + "=" * 85)

        print("INSPECTION COMPLETED")

    finally:

        db.close()


if __name__ == "__main__":
    main()