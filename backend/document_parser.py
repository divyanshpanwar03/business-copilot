from pathlib import Path

from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent.parent

PDF_FILE = (
    BASE_DIR
    / "data"
    / "documents"
    / "labour"
    / "social_security_code_2020.pdf"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "documents"
    / "labour"
    / "social_security_code_2020.txt"
)


reader = PdfReader(PDF_FILE)

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text()

        file.write(
            f"\n--- PAGE {page_number} ---\n\n"
        )

        if text:
            file.write(text)

        file.write("\n")

print(
    f"Extracted {len(reader.pages)} pages "
    f"to {OUTPUT_FILE}"
)