from retriever import search_chunks
from retrieval_eval import get_chunk_text, get_page_number


# ==================================================
# QUESTIONS THAT FAILED OUR EVALUATION
# ==================================================

FAILED_CASES = [
    {
        "question": (
            "How does the Code define an inter-State migrant worker?"
        ),
        "expected_page": 14,
    },
    {
        "question": (
            "Which activities are included in the definition "
            "of a manufacturing process?"
        ),
        "expected_page": 14,
    },
    {
        "question": (
            "How much continuous service is generally required "
            "for gratuity to become payable?"
        ),
        "expected_page": 44,
    },
    {
        "question": (
            "When is completion of five years of continuous "
            "service not necessary for gratuity?"
        ),
        "expected_page": 44,
    },
    {
        "question": (
            "What special service-duration provision applies "
            "to working journalists under the gratuity provisions?"
        ),
        "expected_page": 44,
    },
]


# ==================================================
# CONFIGURATION
# ==================================================

MODES = ["vector", "keyword", "hybrid"]

TOP_K = 5
CANDIDATE_K = 20


# ==================================================
# RUN DIAGNOSTICS
# ==================================================

def main():

    print("\nStarting retrieval diagnostics...", flush=True)

    for mode in MODES:

        print("\n" + "=" * 75, flush=True)
        print(f"RETRIEVAL METHOD: {mode.upper()}", flush=True)
        print("=" * 75, flush=True)

        for case in FAILED_CASES:

            question = case["question"]
            expected_page = case["expected_page"]

            print(f"\nQuestion: {question}", flush=True)
            print(f"Expected page: {expected_page}", flush=True)

            results = search_chunks(
                question,
                top_k=TOP_K,
                candidate_k=CANDIDATE_K,
                mode=mode,
            )

            if not results:
                print("No results returned.", flush=True)
                continue

            expected_page_found = False

            for rank, result in enumerate(results, start=1):

                page = get_page_number(result)

                text = " ".join(
                    get_chunk_text(result).split()
                )

                if page == expected_page:
                    expected_page_found = True

                print(
                    f"\nRank: {rank} | Page: {page}",
                    flush=True,
                )

                # Keep previews short enough to compare easily.
                print(
                    f"Preview: {text[:300]}",
                    flush=True,
                )

            if expected_page_found:
                print(
                    f"\nExpected page {expected_page} "
                    "appears in the top five.",
                    flush=True,
                )
            else:
                print(
                    f"\nExpected page {expected_page} "
                    "does not appear in the top five.",
                    flush=True,
                )

    print("\nDiagnostics completed.", flush=True)


if __name__ == "__main__":
    main()