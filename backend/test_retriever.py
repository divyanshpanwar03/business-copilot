from retriever import search_chunks


query = "When does EPF coverage apply?"

results = search_chunks(
    query,
    top_k=5
)

print(f"Question: {query}")

for index, result in enumerate(results, start=1):

    chunk = result["chunk"]

    print(f"\n--- RESULT {index} ---")
    print(f"Page: {chunk.page_number}")
    print(f"RRF score: {result['rrf_score']:.6f}")

    if result["vector_distance"] is not None:
        print(
            f"Vector distance: "
            f"{result['vector_distance']:.4f}"
        )

    if result["vector_rank"] is not None:
        print(f"Vector rank: {result['vector_rank']}")

    if result["keyword_rank"] is not None:
        print(f"Keyword rank: {result['keyword_rank']}")

    print("\nChunk text:")
    print(chunk.chunk_text[:800])