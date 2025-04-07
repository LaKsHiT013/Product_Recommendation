import os
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone, ServerlessSpec


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
CSV_PATH = "Prod_Cat.csv"
INDEX_NAME = "shl-assessment"
EMBED_MODEL = "models/embedding-001"

pc = Pinecone(api_key=PINECONE_API_KEY)

if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

index = pc.Index(INDEX_NAME)

embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBED_MODEL,
    google_api_key=GOOGLE_API_KEY
)

df = pd.read_csv(CSV_PATH)
docs = df.apply(lambda row: f"Product: {row['Product']}\nDescription: {row['Description']}\nJob Level: {row['Job Level']}\nLanguage: {row['Language']}\nAssessment Length: {row['Assessment Length']}", axis=1)

batch_size = 32
vectors = []
for i in range(0, len(docs), batch_size):
    batch = docs[i:i+batch_size]
    embeds = embeddings.embed_documents(batch.tolist())
    for j, embed in enumerate(embeds):
        vectors.append({
            "id": f"doc-{i+j}",
            "values": embed,
            "metadata": {
                "text": batch.iloc[j]
            }
        })
index.upsert(vectors)
print(f"✅ Inserted {len(vectors)} vectors into Pinecone index '{INDEX_NAME}'")
