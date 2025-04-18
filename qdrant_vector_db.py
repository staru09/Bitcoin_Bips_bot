import pandas as pd
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI
import os
import ollama 
from tqdm import tqdm


# Set your OpenAI API key for using OpenAI for embedding generation
# os.getenv('OPENAI_API_KEY')
# client = OpenAI()

# Qdrant setup
qdrant = QdrantClient(host="localhost", port=6333, timeout=60.0)  # increase timeout in seconds
collection_name = "my_collection"
vector_size = 768 #1536 for OpenAI

# Step 1: Create Qdrant collection
def create_collection(name: str, vector_size: int):
    existing = qdrant.get_collections().collections
    if name not in [c.name for c in existing]:
        qdrant.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
        )
        print(f"Created collection: {name}")
    else:
        print(f"Collection '{name}' already exists")

# Step 2: Get embedding from summary (Uncomment for OpenAI models)

# def get_embedding(text: str) -> list[float]:
#     response = client.embeddings.create(
#         model="text-embedding-3-small",
#         input=text,
#         encoding_format="float"
#     )
#     return response.data[0].embedding

def get_embedding(text: str) -> list[float]:
    response = ollama.embeddings(
        model='nomic-embed-text',
        prompt=text
    )
    return response['embedding']

# Step 3: Read CSV and insert into Qdrant
def insert_from_csv(csv_file: str, batch_size: int = 32):
    df = pd.read_csv(csv_file)
    total = len(df)
    for i in tqdm(range(0, total, batch_size), desc="Inserting in batches"):
        batch = df.iloc[i:i+batch_size]
        points = []
        for _, row in batch.iterrows():
            full = row[0]
            summary = row[1]
            embedding = get_embedding(summary)
            payload = {
                "source": full,
                "summary": summary
            }

            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload=payload
            ))

        try:
            qdrant.upsert(collection_name=collection_name, points=points)
        except Exception as e:
            print(f"Failed batch {i}–{i+batch_size}: {e}")


create_collection(collection_name, vector_size)
insert_from_csv("/home/staru/Desktop/Bitcoin_Bips_bot/data/bips_augmented.csv") 
