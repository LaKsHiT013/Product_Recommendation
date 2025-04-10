import os
import json
import time
from pathlib import Path
from collections import OrderedDict
import streamlit as st
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Constants and configuration
PRODUCTS_JSON_PATH = Path("JSONs/products.json")
INDEX_NAME = "shl-product-index"
DIMENSION = 768
REGION = "us-east-1"
SIMILARITY_THRESHOLD = 0.5
MAX_RECOMMENDATIONS = 7

def load_products(filepath: Path):
    with filepath.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["id"]: item for item in data}

products_db = load_products(PRODUCTS_JSON_PATH)

pc = Pinecone(api_key=PINECONE_API_KEY)
if INDEX_NAME not in pc.list_indexes().names():
    st.write(f"Creating index '{INDEX_NAME}' ...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=REGION)
    )
    # Wait for the index to be created
    while INDEX_NAME not in pc.list_indexes().names():
        time.sleep(1)
else:
    st.write(f"Index '{INDEX_NAME}' already exists.")

index = pc.Index(INDEX_NAME)

embedder = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY
)

def get_recommendations(query: str):
    query = query.strip()
    if not query:
        return {"error": "Missing or empty 'query' field."}
    
    # Get the embedding for the query
    query_embedding = embedder.embed_query(query)
    search_response = index.query(
        vector=query_embedding,
        top_k=MAX_RECOMMENDATIONS,
        include_metadata=False
    )
    
    # Filter matches using the similarity threshold
    filtered_matches = [
        match for match in search_response.get("matches", [])
        if match.get("score", 0) >= SIMILARITY_THRESHOLD
    ]
    
    recommended = []
    for match in filtered_matches:
        product_id = match["id"]
        product = products_db.get(product_id)
        if product:
            rec = OrderedDict([
                ("url", product.get("url", "")),
                ("adaptive_support", product.get("adaptive_support", "")),
                ("description", product.get("description", "")),
                ("duration", int(product.get("duration", 0))),
                ("remote_support", product.get("remote_support", "")),
                ("test_type", product.get("test_type", []))
            ])
            recommended.append(rec)
    
    if not recommended:
        return {"error": "No recommendations found above the similarity threshold."}
    
    return {"recommended_assessments": recommended}

def main():
    st.title("Product Catalogue Recommendations")
    st.markdown("*Ask questions about the SHL assessment documents.*")
    
    # Use a form so that pressing Enter triggers form submission
    with st.form("search_form"):
        query = st.text_input("Enter your query:")
        submitted = st.form_submit_button("Search")
    
    if submitted:
        if not query:
            st.error("Please enter a query!")
        else:
            with st.spinner("Processing your request..."):
                response = get_recommendations(query)
            
            if "error" in response:
                st.error(response["error"])
            else:
                results = response["recommended_assessments"]
                if results:
                    st.write("### Recommended Assessments")
                    for i, result in enumerate(results, start=1):
                        with st.expander(f"Result {i}: {result['description'][:50]}..."):
                            st.write(f"**URL:** {result['url']}")
                            st.write(f"**Adaptive Support:** {result['adaptive_support']}")
                            st.write(f"**Description:** {result['description']}")
                            st.write(f"**Duration:** {result['duration']} minutes")
                            st.write(f"**Remote Support:** {result['remote_support']}")
                            st.write(f"**Test Type:** {', '.join(result['test_type'])}")
                else:
                    st.write("No recommendations found.")

if __name__ == "__main__":
    main()
