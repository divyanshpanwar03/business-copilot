from pathlib import Path
import re


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "documents"
    / "labour"
    / "social_security_code_2020.txt"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "documents"
    / "labour"
    / "social_security_code_2020_clean.txt"
)


def clean_text(text):
    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


with open(INPUT_FILE, "r", encoding="utf-8") as file:
    text = file.read()


cleaned_text = clean_text(text)


with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    file.write(cleaned_text)


print(f"Cleaned text saved to: {OUTPUT_FILE}")