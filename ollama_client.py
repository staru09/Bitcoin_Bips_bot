import os
import uuid
import asyncio
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http import models
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
import ollama  

qdrant = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "my_collection"
VECTOR_SIZE = 768  

llm = Ollama(model="llama3.1", request_timeout=360.0)


def get_embedding(text: str) -> List[float]:
    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )
    return response["embedding"]


def search_qdrant(query: str, top_k: int = 3) -> List[str]:
    embedding = get_embedding(query)

    search_result = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=embedding,
        limit=top_k
    )

    return [hit.payload["source"] for hit in search_result]


async def generate_response(user_input: str) -> str:
    context_chunks = search_qdrant(user_input, top_k=3)
    context = "\n---\n".join(context_chunks)

    system_prompt = (
        "You are an expert assistant. Use the following context to answer the user's question as accurately as possible.\n\n"
        f"{context}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    response = ollama.chat(
        model="llama3.1",
        messages=messages
    )

    return response['message']['content'].strip()

async def chat_loop():
    print("🤖 RAG Chatbot (LLaMA 3.1 + Ollama Embeddings) is ready. Type your question or 'exit' to quit.\n")

    while True:
        query = input("You: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break
        if not query:
            continue

        try:
            answer = await generate_response(query)
            print(f"🤖 Bot: {answer}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    asyncio.run(chat_loop())
