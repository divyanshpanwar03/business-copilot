from retriever import search_chunks


query = "When does EPF coverage apply?"

results = search_chunks(
    query,
    top_k=5
)


for index, chunk in enumerate(
    results,
    start=1
):
    print(f"\n--- RESULT {index} ---")
    print(f"Page: {chunk.page_number}")
    print(f"Distance: {chunk.embedding}")
    print(chunk.chunk_text[:1000])