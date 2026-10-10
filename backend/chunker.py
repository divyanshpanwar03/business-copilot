import re
from pathlib import Path


# ============================================================
# 1. CONFIGURATION
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

DEFAULT_INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "documents"
    / "labour"
    / "social_security_code_2020_clean.txt"
)

DEFAULT_CHUNK_SIZE = 1500


# ============================================================
# 2. REGULAR EXPRESSIONS FOR DOCUMENT STRUCTURE
# ============================================================

# Identifies the page markers added by document_parser.py.
PAGE_MARKER_RE = re.compile(
    r"---\s*PAGE\s+(\d+)\s*---",
    re.IGNORECASE,
)

# Identifies numbered legal definitions, for example:
# (35) "gig worker" means ...
# (41) "inter-State migrant worker" means ...
DEFINITION_START_RE = re.compile(
    r"(?<!\S)\(\d{1,3}\)\s*[“\"‘']"
    r"\s*[^”\"’']{2,120}?[”\"’']"
    r"\s*(?:means|shall mean)\b",
    re.IGNORECASE,
)

# Identifies statutory section headings, for example:
# 52. Appeal to High Court.—
# 53. Payment of gratuity.—
SECTION_START_RE = re.compile(
    r"(?<!\S)\d{1,3}\.\s+"
    r"[A-Z][^.;\n]{1,100}?"
    r"(?:—|–|-)(?=\s|$)"
)

# Identifies chapter headings.
CHAPTER_START_RE = re.compile(
    r"(?<!\S)CHAPTER\s+"
    r"(?:[IVXLCDM]+|\d+)\b",
    re.IGNORECASE,
)


# ============================================================
# 3. READ THE DOCUMENT'S PAGES
# ============================================================

def extract_pages(text):
    """
    Split extracted document text into pages.

    Returns:
        A list of tuples:
        (page_number, page_text)

    Page numbers come from the markers created during parsing.
    """

    matches = list(PAGE_MARKER_RE.finditer(text))

    if not matches:
        raise ValueError(
            "No page markers were found in the input text. "
            "Expected markers such as '--- PAGE 14 ---'. "
            "Check that the cleaned text file came from "
            "document_parser.py."
        )

    pages = []

    for index, match in enumerate(matches):

        page_number = int(match.group(1))

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)

        page_text = text[start:end].strip()

        if page_text:
            pages.append(
                (page_number, page_text)
            )

    return pages


# ============================================================
# 4. FIND LEGAL STRUCTURE BOUNDARIES
# ============================================================

def find_structure_boundaries(page_text):
    """
    Find positions where a new legal unit begins.

    Recognized structures:
        1. Numbered statutory sections.
        2. Numbered definitions.
        3. Chapter headings.

    This helps prevent unrelated provisions from being
    grouped into the same chunk.
    """

    boundaries = set()

    patterns = [
        SECTION_START_RE,
        DEFINITION_START_RE,
    ]

    for pattern in patterns:

        for match in pattern.finditer(page_text):

            boundaries.add(match.start())

    return sorted(boundaries)


# ============================================================
# 5. SPLIT LARGE LEGAL UNITS
# ============================================================

def split_large_unit(text, chunk_size):
    """
    Split an oversized legal unit into smaller pieces.

    First, try to split at sentence or clause boundaries.
    If a single piece is still too large, split at word
    boundaries.

    Short legal units remain intact.
    """

    text = " ".join(text.split())

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    # Preserve punctuation while splitting at likely clause
    # or sentence boundaries.
    pieces = re.split(
        r"(?<=[.;])\s+",
        text,
    )

    chunks = []
    current = ""

    for piece in pieces:

        piece = piece.strip()

        if not piece:
            continue

        # A single sentence or clause might exceed the target.
        if len(piece) > chunk_size:

            if current:
                chunks.append(current)
                current = ""

            # Split exceptionally long pieces at word boundaries.
            words = piece.split()

            part = ""

            for word in words:

                if part and len(part) + 1 + len(word) > chunk_size:

                    chunks.append(part)
                    part = word

                else:

                    part = (
                        f"{part} {word}"
                        if part
                        else word
                    )

            if part:
                current = part

            continue

        # Add a clause if it fits in the current chunk.
        if not current:

            current = piece

        elif len(current) + 1 + len(piece) <= chunk_size:

            current = f"{current} {piece}"

        else:

            chunks.append(current)
            current = piece

    if current:
        chunks.append(current)

    return chunks


# ============================================================
# 6. CREATE STRUCTURE-AWARE CHUNKS FOR ONE PAGE
# ============================================================

def chunk_page(page_number, page_text, chunk_size=DEFAULT_CHUNK_SIZE):
    """
    Convert one page into structure-aware chunks.

    Legal sections and definitions are separated where
    recognizable. Oversized units are split further.

    Each returned dictionary preserves the page number.
    """

    page_text = " ".join(page_text.split())

# Remove a duplicate printed page number at the start of the page.
    page_text = re.sub(
        rf"^{page_number}\s+",
        "",
        page_text,
    )
    if not page_text:
        return []

    boundaries = find_structure_boundaries(page_text)

    # If no recognizable legal structures exist, use the
    # available text and split it by size.
    if not boundaries:

        units = [page_text]

    else:

        positions = [0] + boundaries + [len(page_text)]

        units = []

        for index in range(len(positions) - 1):

            start = positions[index]
            end = positions[index + 1]

            unit = page_text[start:end].strip()

            if unit:
                units.append(unit)

    page_chunks = []

    for unit in units:

        smaller_chunks = split_large_unit(
            unit,
            chunk_size,
        )

        for chunk_text in smaller_chunks:

            page_chunks.append(
                {
                    "text": chunk_text,
                    "page_number": page_number,
                }
            )

    return page_chunks


# ============================================================
# 7. CHUNK A COMPLETE DOCUMENT FROM TEXT
# ============================================================

def chunk_text(text, chunk_size=DEFAULT_CHUNK_SIZE):
    """
    Chunk the complete extracted document text.

    Input:
        Text containing page markers.

    Output:
        A list of dictionaries:
        {
            "text": "...",
            "page_number": 14
        }
    """

    if not isinstance(text, str):
        raise TypeError(
            "chunk_text() expects a string containing "
            "the extracted document text."
        )

    if chunk_size < 100:
        raise ValueError(
            "chunk_size must be at least 100 characters."
        )

    pages = extract_pages(text)

    all_chunks = []

    for page_number, page_text in pages:

        page_chunks = chunk_page(
            page_number,
            page_text,
            chunk_size=chunk_size,
        )

        all_chunks.extend(page_chunks)

    return all_chunks


# ============================================================
# 8. CHUNK A DOCUMENT FROM A FILE
# ============================================================

def chunk_document(
    file_path=DEFAULT_INPUT_PATH,
    chunk_size=DEFAULT_CHUNK_SIZE,
):
    """
    Read the cleaned document and return its chunks.

    This function does not write anything to PostgreSQL.
    It only creates chunk dictionaries in Python memory.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Cleaned document not found: {file_path}"
        )

    text = file_path.read_text(
        encoding="utf-8-sig"
    )

    return chunk_text(
        text,
        chunk_size=chunk_size,
    )


# ============================================================
# 9. PREVIEW THE NEW CHUNKS
# ============================================================
def validate_important_passages(chunks):
    """
    Check whether important legal passages remain together
    in at least one newly generated chunk.
    """

    test_cases = [
        {
            "name": "Inter-State migrant worker",
            "terms": [
                "inter-state migrant worker",
                "recruited directly by the employer or indirectly through contractor",
                "destination state",
            ],
        },
        {
            "name": "Manufacturing process",
            "terms": [
                "manufacturing process",
                "making, altering, repairing",
                "pumping oil, water, sewage",
                "preserving or storing any article in cold storage",
            ],
        },
        {
            "name": "Gratuity eligibility",
            "terms": [
                "gratuity shall be payable to an employee",
                "continuous service for not less than five years",
            ],
        },
        {
            "name": "Gratuity exceptions",
            "terms": [
                "completion of continuous service of five years shall not be necessary",
                "expiration of fixed term employment",
            ],
        },
        {
            "name": "Working journalist provision",
            "terms": [
                "working journalist",
                '"five years" occurring in this sub-section shall be deemed to be three years',
            ],
        },
        {
            "name": "EPF applicability",
            "terms": [
                "employees' provident fund",
                "twenty or more employees",
            ],
        },
        {
            "name": "ESI applicability",
            "terms": [
                "employees' state insurance corporation",
                "ten or more persons",
            ],
        },
    ]

    def normalize(text):
        text = str(text).casefold()

        text = (
            text.replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
        )

        return " ".join(text.split())

    print("\nVERIFYING IMPORTANT PASSAGES")
    print("=" * 70)

    for case in test_cases:

        expected_terms = [
            normalize(term)
            for term in case["terms"]
        ]

        matching_chunks = []

        for chunk in chunks:

            chunk_text = normalize(chunk["text"])

            if all(
                term in chunk_text
                for term in expected_terms
            ):
                matching_chunks.append(chunk)

        print(f"\n{case['name']}")

        if matching_chunks:

            for chunk in matching_chunks:

                print(
                    f"PASS | Page {chunk['page_number']} | "
                    f"{len(chunk['text'])} characters"
                )

        else:

            print(
                "CHECK | Expected phrases were not all found "
                "together in one chunk."
            )

    # Report unusually short chunks for inspection.
    short_chunks = [
        (index, chunk)
        for index, chunk in enumerate(chunks, start=1)
        if len(chunk["text"].strip()) < 20
    ]

    print("\n" + "=" * 70)
    print(
        f"Chunks shorter than 20 characters: {len(short_chunks)}"
    )

    for index, chunk in short_chunks[:10]:

        print(
            f"Chunk {index} | Page {chunk['page_number']} | "
            f"Text: {chunk['text']!r}"
        )

    if len(short_chunks) > 10:
        print("Only the first 10 short chunks are shown.")

def main():

    print("\nSTRUCTURE-AWARE CHUNKING PREVIEW")
    print("=" * 75)

    print(f"Input document: {DEFAULT_INPUT_PATH}")
    print(f"Target chunk size: {DEFAULT_CHUNK_SIZE}")

    chunks = chunk_document()
    validate_important_passages(chunks)

    print(f"\nTotal chunks created: {len(chunks)}")

    print(
        f"Original stored chunks: 224 "
        "(reference from our previous database inspection)"
    )

    lengths = [
        len(chunk["text"])
        for chunk in chunks
    ]

    if lengths:

        print(f"Smallest chunk: {min(lengths)} characters")
        print(f"Largest chunk: {max(lengths)} characters")

        print(
            "Average chunk size: "
            f"{sum(lengths) / len(lengths):.1f} characters"
        )

    # Inspect the pages containing the provisions that
    # previously caused problems.
    pages_to_inspect = {14, 44, 97}

    print("\n" + "=" * 75)
    print("INSPECTING IMPORTANT LEGAL PASSAGES")
    print("=" * 75)

    for chunk_number, chunk in enumerate(chunks, start=1):

        if chunk["page_number"] not in pages_to_inspect:
            continue

        print("\n" + "-" * 75)

        print(
            f"New chunk: {chunk_number} | "
            f"Page: {chunk['page_number']} | "
            f"Length: {len(chunk['text'])} characters"
        )

        print(chunk["text"][:700])

        if len(chunk["text"]) > 700:
            print("... [preview truncated]")

    print("\n" + "=" * 75)
    print("PREVIEW COMPLETED")
    print("No database records were changed.")


if __name__ == "__main__":
    main()