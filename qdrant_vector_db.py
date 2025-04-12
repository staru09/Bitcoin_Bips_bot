import pandas as pd
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI
import os

# Set your OpenAI API key
os.getenv('OPENAI_API_KEY')
client = OpenAI()

# Qdrant setup
qdrant = QdrantClient(host="localhost", port=6333) 
collection_name = "my_collection"
vector_size = 1536 

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

# Step 2: Get embedding from summary
def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        encoding_format="float"
    )
    return response.data[0].embedding

# Step 3: Read CSV and insert into Qdrant
def insert_from_csv(csv_file: str):
    df = pd.read_csv(csv_file)
    points = []
    for _, row in df.iterrows():
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

    qdrant.upsert(collection_name=collection_name, points=points)
    print(f"Inserted {len(points)} records into Qdrant")

# === RUN ===
create_collection(collection_name, vector_size)
insert_from_csv(r"C:\Users\91745\OneDrive\Desktop\Bitcoin_bips_bot\data\test.csv") 
