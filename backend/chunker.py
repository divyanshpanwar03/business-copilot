from pathlib import Path
import re


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "documents"
    / "labour"
    / "social_security_code_2020_clean.txt"
)

CHUNK_SIZE = 1500


def split_into_pages(text):
    pages = []

    page_blocks = re.split(
        r"--- PAGE (\d+) ---",
        text
    )

    for i in range(1, len(page_blocks), 2):
        page_number = int(page_blocks[i])
        page_text = page_blocks[i + 1].strip()

        pages.append({
            "page_number": page_number,
            "text": page_text
        })

    return pages


def split_into_paragraphs(text):
    paragraphs = re.split(
        r"\n\s*\n",
        text
    )

    cleaned_paragraphs = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if paragraph:
            cleaned_paragraphs.append(paragraph)

    return cleaned_paragraphs


def create_chunks(text):
    pages = split_into_pages(text)

    chunks = []

    for page in pages:

        paragraphs = split_into_paragraphs(
            page["text"]
        )

        current_chunk = ""
        page_number = page["page_number"]

        for paragraph in paragraphs:

            if (
                len(current_chunk)
                + len(paragraph)
                + 2
                <= CHUNK_SIZE
            ):
                if current_chunk:
                    current_chunk += "\n\n"

                current_chunk += paragraph

            else:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk,
                        "page_number": page_number
                    })

                current_chunk = paragraph

        if current_chunk:
            chunks.append({
                "text": current_chunk,
                "page_number": page_number
            })

    return chunks


def load_chunks():
    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        text = file.read()

    return create_chunks(text)

if __name__ == "__main__":
    chunks = load_chunks()
    print(
        f"Created {len(chunks)} chunks."
    )
    for index, chunk in enumerate(
        chunks[:5],
        start=1
    ):
        print(
            f"\n--- CHUNK {index} ---"
        )
        print(
            f"Page: {chunk['page_number']}"
        )
        print(
            chunk["text"][:500]
        )