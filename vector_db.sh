#!/bin/bash

# Install WasmEdge Runtime
echo "Installing WasmEdge Runtime..."
curl -sSf https://raw.githubusercontent.com/WasmEdge/WasmEdge/master/utils/install_v2.sh | bash -s -- --ggmlcuda=12

# Download embedding model
echo "Downloading embedding model..."
curl -LO https://huggingface.co/gaianet/Nomic-embed-text-v1.5-Embedding-GGUF/resolve/main/nomic-embed-text-v1.5.f16.gguf

# Start Qdrant vector database using Docker
echo "Starting Qdrant vector database..."
mkdir -p qdrant_storage
mkdir -p qdrant_snapshots

nohup docker run -d -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    -v $(pwd)/qdrant_snapshots:/qdrant/snapshots:z \
    qdrant/qdrant > qdrant.log 2>&1 &

# Wait for Qdrant to start
sleep 10

# Delete default collection if it exists
echo "Setting up vector collection..."
curl -X DELETE 'http://localhost:6333/collections/default'

# Create new collection
curl -X PUT 'http://localhost:6333/collections/default' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "vectors": {
      "size": 768,
      "distance": "Cosine",
      "on_disk": true
    }
  }'

# Download embedding tool
echo "Downloading embedding tool..."
curl -LO https://github.com/GaiaNet-AI/embedding-tools/raw/main/csv_embed/csv_embed.wasm

# Process document and create embeddings
wasmedge --dir .:. \
  --nn-preload embedding:GGML:AUTO:nomic-embed-text-v1.5.f16.gguf \
  paragraph_embed.wasm embedding default 768 bips_augmented.csv -c 8192

# Create snapshot
echo "Creating vector snapshot..."
curl -X POST 'http://localhost:6333/collections/default/snapshots'
