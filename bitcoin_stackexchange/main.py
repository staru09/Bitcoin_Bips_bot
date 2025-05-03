from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from chromadb.utils import embedding_functions
import requests
import os
from huggingface_hub import login

class NomicEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, hf_token):
        login(token=hf_token)
        
        self.model = HuggingFaceEmbedding(
            model_name="nomic-ai/nomic-embed-text-v2-moe",
            trust_remote_code=True
        )
    
    def __call__(self, texts):
        prefixed_texts = [f"search_document: {text}" for text in texts]
        return self.model.get_text_embedding_batch(prefixed_texts)

class BitcoinChatbot:
    def __init__(self, db_path="./bitcoin_stack_db", hf_token=None):
        if not hf_token:
            hf_token = os.getenv('HUGGINGFACE_TOKEN')
            if not hf_token:
                raise ValueError("Please provide a HuggingFace token either directly or via HUGGINGFACE_TOKEN environment variable")
        
        self.embedding_function = NomicEmbeddingFunction(hf_token)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection(
            name="bitcoin_stack_exchange",
            embedding_function=self.embedding_function
        )
        
        self.ollama_host = "http://172.16.10.24:11434"
        print(f"Database loaded with {self.collection.count()} documents")

    def get_response(self, query):
        results = self.collection.query(
            query_texts=[f"search_document: {query}"],
            n_results=5
        )
        
        contexts = []
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            contexts.append(f"Document {i+1} [Score: {metadata['score']}]:\n{doc}")
        
        context = "\n\n".join(contexts)
        
        prompt = f"""You are a Bitcoin expert assistant. Answer questions using the provided Bitcoin Stack Exchange data.
        
Question: {query}

Relevant information:
{context}

Please provide a comprehensive answer based on the above information. 
Include technical details, security considerations, and best practices where relevant.

Answer:"""

        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": "llama3.3", 
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2048,
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json()['response'], results
            else:
                return f"Error: Failed to get response (Status code: {response.status_code})", None
                
        except Exception as e:
            return f"Error: {str(e)}", None

def main():
    hf_token = os.getenv('HUGGINGFACE_TOKEN')
    if not hf_token:
        hf_token = input("Please enter your HuggingFace token: ").strip()
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("Bitcoin Stack Exchange Chatbot")
    print("=============================")
    print("Type 'quit' to exit")
    print("Type 'clear' to clear screen")
    print("Type 'sources' to see sources of last response")
    
    try:
        chatbot = BitcoinChatbot(hf_token=hf_token)
    except Exception as e:
        print(f"Error initializing chatbot: {str(e)}")
        return
    
    last_results = None
    
    while True:
        try:
            query = input("\nYou: ").strip()
            
            if query.lower() == 'quit':
                break
                
            if query.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
                
            if query.lower() == 'sources' and last_results:
                print("\nSources:")
                print("========")
                for i, (doc, metadata) in enumerate(zip(last_results['documents'][0], last_results['metadatas'][0])):
                    print(f"\nSource {i+1}:")
                    print("-" * 80)
                    print(f"Score: {metadata['score']}")
                    print(f"Document ID: {metadata['doc_id']}")
                    print("-" * 80)
                    print(doc[:300] + "..." if len(doc) > 300 else doc)
                continue
            
            if not query:
                continue
            
            print("\nThinking...")
            response, results = chatbot.get_response(query)
            last_results = results
            
            print("\nResponse:")
            print("=========")
            print(response)
            print("\nType 'sources' to see the source documents")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()

