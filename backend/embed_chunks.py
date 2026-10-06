from sentence_transformers import SentenceTransformer
from chunker import load_chunks


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


model = SentenceTransformer(MODEL_NAME)

chunks = load_chunks()

texts=[]

for chunk in chunks:
    texts.append(chunk["text"])

embeddings = model.encode(texts)

print("Number of chunks:", len(chunks))
print("Embedding shape:", embeddings.shape)

print("\nFirst chunk:")
print(chunks[0]["text"][:500])

print("\nFirst embedding:")
print(embeddings[0])

print("\nEmbedding length:")
print(len(embeddings[0]))