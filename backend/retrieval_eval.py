import sys

# ============================================================
# 1. WINDOWS CONSOLE ENCODING
# ============================================================

# Prevent special characters extracted from PDFs from crashing
# the evaluation when they cannot be printed in the console.

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(errors="replace")


from retriever import search_chunks


# ============================================================
# 2. CONFIGURATION
# ============================================================

TOP_K = 5
CANDIDATE_K = 20

MODES = ["vector", "keyword", "hybrid"]


# ============================================================
# 3. EVALUATION DATASET
# ============================================================

EVALUATION_CASES = [

    # --------------------------------------------------------
    # EPF AND ESI APPLICABILITY
    # --------------------------------------------------------

    {
        "question": "When does EPF coverage apply?",
        "expected_pages": [97],
        "expected_terms": [
            "employees' provident fund",
            "twenty or more employees",
        ],
    },

    {
        "question": "When does ESI coverage apply?",
        "expected_pages": [97],
        "expected_terms": [
            "employees' state insurance corporation",
            "ten or more persons",
        ],
    },

    {
        "question": (
            "Can ESI apply to an establishment that employs "
            "only one person?"
        ),
        "expected_pages": [97],
        "expected_terms": [
            "hazardous or life threatening occupation",
            "even a single employee is employed",
        ],
    },

    {
        "question": (
            "When can an employer of a plantation "
            "opt for ESI coverage?"
        ),
        "expected_pages": [97],
        "expected_terms": [
            "employer of a plantation",
            "benefits available to the employees under "
            "that Chapter are better",
        ],
    },

    {
        "question": (
            "When do employer and employee contributions "
            "become payable under Chapter IV?"
        ),
        "expected_pages": [97],
        "expected_terms": [
            "contribution from the employers and employees",
            "date on which any benefits under Chapter IV",
            "provided by the Corporation to the employees",
        ],
    },


    # --------------------------------------------------------
    # DEFINITIONS OF WORKERS
    # --------------------------------------------------------

    {
        "question": "What is a gig worker?",
        "expected_pages": [14],
        "expected_terms": [
            "gig worker",
            "outside of traditional employer-employee relationship",
        ],
    },

    {
        "question": "Who qualifies as a home-based worker?",
        "expected_pages": [14],
        "expected_terms": [
            "home-based worker",
            "production of goods or services for an employer in his home",
            "other premises of his choice other than the workplace "
            "of the employer",
        ],
    },

    {
        "question": (
            "How does the Code define an inter-State migrant worker?"
        ),
        "expected_pages": [14],
        "expected_terms": [
            "inter-state migrant worker",
            "recruited directly by the employer or indirectly "
            "through contractor",
            "destination state",
        ],
    },

    {
        "question": (
            "Which activities are included in the definition "
            "of a manufacturing process?"
        ),
        "expected_pages": [14],
        "expected_terms": [
            "manufacturing process",
            "making, altering, repairing",
            "pumping oil, water, sewage",
            "preserving or storing any article in cold storage",
        ],
    },


    # --------------------------------------------------------
    # EMPLOYEES' INSURANCE COURT AND APPEALS
    # --------------------------------------------------------

    {
        "question": (
            "What is the limitation period for proceedings "
            "before the Employees' Insurance Court?"
        ),
        "expected_pages": [44],
        "expected_terms": [
            "employees' insurance court",
            "three years from the date",
        ],
    },

    {
        "question": (
            "When can an appeal be filed before the High Court "
            "against an order of the Employees' Insurance Court?"
        ),
        "expected_pages": [44],
        "expected_terms": [
            "appeal shall lie to the High Court",
            "substantial question of law",
        ],
    },

    {
        "question": (
            "Within what period must an appeal to the High Court "
            "be filed under section 52?"
        ),
        "expected_pages": [44],
        "expected_terms": [
            "within a period of sixty days",
            "date of the order made by the Employees' Insurance Court",
        ],
    },

    {
        "question": (
            "Who may represent a person before the "
            "Employees' Insurance Court?"
        ),
        "expected_pages": [44],
        "expected_terms": [
            "legal practitioner",
            "officer of a registered trade union",
            "authorised in writing by such person",
        ],
    },


    # --------------------------------------------------------
    # GRATUITY
    # --------------------------------------------------------

    {
        "question": (
            "How much continuous service is generally required "
            "for gratuity to become payable?"
        ),
        "expected_pages": [44],
        "expected_terms": [
            "gratuity shall be payable to an employee",
            "continuous service for not less than five years",
        ],
    },

    {
        "question": (
            "When is completion of five years of continuous service "
            "not necessary for gratuity?"
        ),
        "expected_pages": [44],
        "expected_terms": [
            "completion of continuous service of five years "
            "shall not be necessary",
            "expiration of fixed term employment",
        ],
    },

    {
        "question": (
            "What special service-duration provision applies "
            "to working journalists under the gratuity provisions?"
        ),
        "expected_pages": [44],
        "expected_terms": [
            "working journalist",
            '"five years" occurring in this sub-section '
            "shall be deemed to be three years",
        ],
    },

]


# ============================================================
# 4. TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    """
    Normalize text before searching for expected phrases.

    This handles:
    - Uppercase and lowercase differences
    - Curly and straight quotation marks
    - Extra whitespace and line breaks
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
# 5. EXTRACT INFORMATION FROM A RETRIEVAL RESULT
# ============================================================

def get_chunk(result):
    """
    The retriever returns a dictionary containing a chunk
    under the 'chunk' key.

    Extract that chunk while also supporting a direct chunk
    object or dictionary.
    """

    if isinstance(result, dict):
        return result.get("chunk", result)

    return result


def get_chunk_text(result):
    """Return the text of a retrieved chunk."""

    chunk = get_chunk(result)

    if isinstance(chunk, dict):
        return chunk.get(
            "chunk_text",
            chunk.get("text", ""),
        )

    return getattr(chunk, "chunk_text", "")


def get_page_number(result):
    """Return the page number associated with a chunk."""

    chunk = get_chunk(result)

    if isinstance(chunk, dict):
        return chunk.get("page_number")

    return getattr(chunk, "page_number", None)


# ============================================================
# 6. CHECK WHETHER A RETRIEVED CHUNK IS RELEVANT
# ============================================================

def is_relevant(result, evaluation_case):
    """
    A result counts as relevant if every expected phrase
    appears in its text.

    The expected page is kept as reference information,
    but it is NOT used as a pass/fail condition.

    Important limitation:
    All expected phrases must occur in the same chunk.
    """

    chunk_text = normalize_text(
        get_chunk_text(result)
    )

    expected_terms = evaluation_case.get(
        "expected_terms",
        [],
    )

    # We cannot verify relevance without expected phrases.
    if not expected_terms:
        return False

    # Every expected phrase must appear in the chunk.
    for term in expected_terms:

        normalized_term = normalize_text(term)

        if normalized_term not in chunk_text:
            return False

    return True


# ============================================================
# 7. DIAGNOSE WHY A RESULT FAILED
# ============================================================

def diagnose_failed_results(results, evaluation_case):
    """
    When no relevant result is found, inspect each returned chunk.

    For every result, print:
    - Its rank
    - Its page number
    - Which expected phrases are missing
    - A short preview of its text

    This helps distinguish a retrieval problem from an
    overly strict evaluation condition.
    """

    expected_terms = evaluation_case.get(
        "expected_terms",
        [],
    )

    expected_pages = evaluation_case.get(
        "expected_pages",
        [],
    )

    print(
        f"\nReference pages: {expected_pages}",
        flush=True,
    )

    print(
        f"Expected phrases: {expected_terms}",
        flush=True,
    )

    print(
        "\nChecking each retrieved result:",
        flush=True,
    )

    for rank, result in enumerate(results, start=1):

        page_number = get_page_number(result)

        chunk_text = normalize_text(
            get_chunk_text(result)
        )

        missing_terms = [
            term
            for term in expected_terms
            if normalize_text(term) not in chunk_text
        ]

        print(
            f"\nRank: {rank} | Page: {page_number}",
            flush=True,
        )

        if missing_terms:

            print(
                f"Missing phrases: {missing_terms}",
                flush=True,
            )

        else:

            print(
                "All expected phrases found in this chunk.",
                flush=True,
            )

        preview = " ".join(
            get_chunk_text(result).split()
        )

        print(
            f"Preview: {preview[:300]}",
            flush=True,
        )

    print(
        "\nDiagnostic note: missing phrases do not automatically "
        "prove retrieval is broken. The expected phrases or "
        "the chunk boundaries may also need inspection.",
        flush=True,
    )


# ============================================================
# 8. EVALUATE ONE RETRIEVAL METHOD
# ============================================================

def evaluate_mode(mode):
    """
    Evaluate one retrieval method against all test questions.

    Hit Rate@5:
        Fraction of questions with at least one relevant
        result in the top five.

    MRR:
        Mean Reciprocal Rank of the first relevant result.
    """

    total_questions = len(EVALUATION_CASES)

    hit_count = 0
    reciprocal_rank_sum = 0.0

    print("\n" + "=" * 70, flush=True)

    print(
        f"EVALUATING {mode.upper()} SEARCH",
        flush=True,
    )

    print("=" * 70, flush=True)

    for index, case in enumerate(
        EVALUATION_CASES,
        start=1,
    ):

        question = case["question"]

        print(
            f"\nQuestion {index}/{total_questions}: {question}",
            flush=True,
        )

        # ----------------------------------------------------
        # Retrieve results for this question.
        # ----------------------------------------------------

        results = search_chunks(
            question,
            top_k=TOP_K,
            candidate_k=CANDIDATE_K,
            mode=mode,
        )

        if not results:

            print(
                "Retriever returned no results.",
                flush=True,
            )

            print(
                "This question counts as a miss.",
                flush=True,
            )

            continue

        # ----------------------------------------------------
        # Find the first relevant result.
        # ----------------------------------------------------

        relevant_rank = None
        relevant_result = None

        for rank, result in enumerate(
            results,
            start=1,
        ):

            if is_relevant(result, case):

                relevant_rank = rank
                relevant_result = result

                break

        # ----------------------------------------------------
        # Record a successful retrieval.
        # ----------------------------------------------------

        if relevant_result is not None:

            hit_count += 1

            reciprocal_rank_sum += (
                1.0 / relevant_rank
            )

            matched_page = get_page_number(
                relevant_result
            )

            matched_text = get_chunk_text(
                relevant_result
            )

            print(
                f"\nRelevant result found at rank: "
                f"{relevant_rank}",
                flush=True,
            )

            print(
                f"Matched page: {matched_page}",
                flush=True,
            )

            print(
                "Matched chunk:",
                flush=True,
            )

            # Print the actual matching passage so that
            # we can verify that it supports the question.
            print(
                matched_text,
                flush=True,
            )

        # ----------------------------------------------------
        # Diagnose unsuccessful retrieval.
        # ----------------------------------------------------

        else:

            print(
                f"\nNo relevant result found in the "
                f"top {TOP_K}.",
                flush=True,
            )

            diagnose_failed_results(
                results,
                case,
            )

        # ----------------------------------------------------
        # Show the highest-ranked result separately.
        # ----------------------------------------------------

        first_result = results[0]

        first_page = get_page_number(
            first_result
        )

        first_text = " ".join(
            get_chunk_text(first_result).split()
        )

        print(
            f"\nTop-ranked page: {first_page}",
            flush=True,
        )

        print(
            f"Top-ranked preview: {first_text[:250]}",
            flush=True,
        )

    # ========================================================
    # CALCULATE METRICS
    # ========================================================

    if total_questions > 0:

        hit_rate = (
            hit_count / total_questions
        )

        mrr = (
            reciprocal_rank_sum / total_questions
        )

    else:

        hit_rate = 0.0
        mrr = 0.0

    metrics = {
        "mode": mode,
        "hit_rate": hit_rate,
        "mrr": mrr,
        "hits": hit_count,
        "total": total_questions,
    }

    print("\n" + "-" * 70, flush=True)

    print(
        f"{mode.upper()} RESULTS",
        flush=True,
    )

    print("-" * 70, flush=True)

    print(
        f"Hit Rate@{TOP_K}: {hit_rate:.4f}",
        flush=True,
    )

    print(
        f"MRR: {mrr:.4f}",
        flush=True,
    )

    print(
        f"Questions with a hit: "
        f"{hit_count}/{total_questions}",
        flush=True,
    )

    return metrics


# ============================================================
# 9. RUN ALL RETRIEVAL METHODS
# ============================================================

def main():

    print(
        "\nStarting retrieval evaluation...",
        flush=True,
    )

    print(
        f"Evaluation questions: {len(EVALUATION_CASES)}",
        flush=True,
    )

    print(
        f"Top-K: {TOP_K}",
        flush=True,
    )

    print(
        f"Candidate-K: {CANDIDATE_K}",
        flush=True,
    )

    print(
        "\nRelevance is determined by expected phrases, "
        "not by exact page-number matches.",
        flush=True,
    )

    all_metrics = []

    # Run vector, keyword, and hybrid retrieval separately.
    for mode in MODES:

        metrics = evaluate_mode(mode)

        all_metrics.append(metrics)

    # ========================================================
    # FINAL COMPARISON TABLE
    # ========================================================

    print("\n\n" + "=" * 70, flush=True)

    print(
        "FINAL RETRIEVAL COMPARISON",
        flush=True,
    )

    print("=" * 70, flush=True)

    print(
        f"{'Mode':<12}"
        f"{'Hit Rate@5':<16}"
        f"{'MRR':<12}"
        f"{'Hits':<10}",
        flush=True,
    )

    print("-" * 70, flush=True)

    for metrics in all_metrics:

        print(
            f"{metrics['mode']:<12}"
            f"{metrics['hit_rate']:<16.4f}"
            f"{metrics['mrr']:<12.4f}"
            f"{metrics['hits']}/{metrics['total']}",
            flush=True,
        )

    print(
        "\nEvaluation completed.",
        flush=True,
    )


# ============================================================
# 10. SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()