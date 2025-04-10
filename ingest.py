import os
import json
import uuid
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings


load_dotenv()
JSON_PATH = Path("JSONs/products.json")
INDEX_NAME = "shl-product-index"
BATCH_SIZE = 32

def load_json(filepath: Path):
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filepath: Path, data):
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def initialize_pinecone():

    from pinecone import Pinecone, ServerlessSpec

    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating index '{INDEX_NAME}' ...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

        while INDEX_NAME not in pc.list_indexes().names():
            time.sleep(1)
    else:
        print(f"Index '{INDEX_NAME}' already exists.")

    return pc.Index(INDEX_NAME)

def ensure_ids(data):

    for item in data:
        if "id" not in item or not item["id"]:
            new_id = str(uuid.uuid4())
            print(f"Assigning new id {new_id} to item with description: {item.get('description','')}")
            item["id"] = new_id
    return data

def main():

    print("Loading JSON data...")
    data = load_json(JSON_PATH)
    data = ensure_ids(data)
    
    save_json(JSON_PATH, data)
    print(f"Updated JSON saved to {JSON_PATH}")

    embed = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.environ.get("GOOGLE_API_KEY")
    )
    
    index = initialize_pinecone()

    print("Creating embeddings and upserting into Pinecone in batches...")
    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i:i+BATCH_SIZE]
        vectors = []
        for item in batch:
            description = item["description"]
            vector = embed.embed_query(description)
            vectors.append((item["id"], vector, {"description": description}))
        
        index.upsert(vectors)
        print(f"Upserted batch {(i // BATCH_SIZE) + 1} (items {i} to {i + len(batch) - 1}).")
    
    print("All vectors upserted successfully.")

if __name__ == "__main__":
    main()
