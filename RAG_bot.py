import sys
import os
import asyncio
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.workflow import Context
from llama_index.core.node_parser import SentenceSplitter
import chromadb

Settings.embed_model = HuggingFaceEmbedding(
    model_name="nomic-ai/nomic-embed-text-v2-moe", trust_remote_code=True
)
Settings.llm = Ollama(model="llama3.1", request_timeout=360.0)

sentence_splitter = SentenceSplitter(
    chunk_size=1024,              # number of tokens per chunk
    chunk_overlap=200,            # overlap between chunks
    separator=' ',                # how words are split
    paragraph_separator='\n\n\n'  # defines paragraph boundaries
)

documents = SimpleDirectoryReader("./data").load_data()
nodes = sentence_splitter.get_nodes_from_documents(documents)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_or_create_collection("btc")

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex(
    nodes,
    storage_context=storage_context
)


chat_engine = index.as_chat_engine(
    chat_mode="openai", 
    similarity_top_k=10,
    system_prompt="You are a helpful assistant that provides accurate information based on the documents provided.",
    verbose=False
)

async def main():
    print("🤖 Welcome to the Btc Assistant (Ollama + ChromaDB Chat Engine)")
    print("Ask your question or type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break
        if user_input == "":
            continue

        try:
            response = await chat_engine.achat(user_input)
            print(f"Assistant: {response}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
