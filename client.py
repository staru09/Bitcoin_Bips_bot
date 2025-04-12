import os
import uuid
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List

# Environment
os.getenv('OPENAI_API_KEY')
client = OpenAI()
qdrant = QdrantClient(host="localhost", port=6333)

COLLECTION_NAME = "my_collection"

# Get embedding from OpenAI
def get_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        encoding_format="float"
    )
    return response.data[0].embedding

# Search Qdrant with embedding
def search_qdrant(query: str, top_k: int = 3) -> List[str]:
    embedding = get_embedding(query)

    search_result = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=embedding,
        limit=top_k
    )

    return [hit.payload["source"] for hit in search_result]

# Generate response with GPT-4o-mini
def generate_response(user_input: str) -> str:
    context_chunks = search_qdrant(user_input, top_k=3)
    context = "\n---\n".join(context_chunks)

    system_prompt = (
        "You are an expert assistant. Use the following context to answer the user's question as accurately as possible.\n\n"
        f"{context}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content.strip()


def chat_loop():
    """Simple loop for chatting with the bot"""
    print("📚 RAG Bot is ready! Ask me something (type 'exit' to quit):\n")
    while True:
        query = input("You: ")
        if query.lower() in {"exit", "quit"}:
            print("👋 Exiting. Goodbye!")
            break

        try:
            response = generate_response(query)
            print(f"🤖 Bot: {response}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    chat_loop()