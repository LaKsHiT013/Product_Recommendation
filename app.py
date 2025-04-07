import streamlit as st
import re
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import Pinecone
from dotenv import load_dotenv
import os
from pinecone import Pinecone as PineconeClient, ServerlessSpec

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
INDEX_NAME = "shl-assessment"

# Initialize Pinecone client
pc = PineconeClient(api_key=PINECONE_API_KEY)

# Check and create index if it does not exist
existing_indexes = [idx.name for idx in pc.list_indexes()]
if INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=INDEX_NAME,
        dimension=3072,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    )

# Initialize embeddings and docsearch interface
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY
)

docsearch = Pinecone.from_existing_index(
    index_name=INDEX_NAME,
    embedding=embeddings,
    text_key="text"
)

# This function simulates the call to Gemini (or any LLM) to format the raw text.
# In practice, replace this with the actual API call to your language model.
def gemini_format_product(raw_text):
    # Use regex patterns to extract fields from the raw text.
    product_match = re.search(r"(Product:\s*[^D]+)", raw_text)
    description_match = re.search(r"Description:\s*(.+?)\s*Job Level:", raw_text)
    job_level_match = re.search(r"Job Level:\s*([^,]+(?:,\s*[^,]+)*)", raw_text)
    language_match = re.search(r"Language:\s*([^,]+)", raw_text)
    assessment_match = re.search(r"Assessment Length:.*?max\s*(\d+)", raw_text, re.IGNORECASE)

    product = product_match.group(1).strip() if product_match else "Product information not found."
    description = description_match.group(1).strip() if description_match else "Description not found."
    job_level = job_level_match.group(1).strip() if job_level_match else "Job level not found."
    language = language_match.group(1).strip() if language_match else "Language not found."
    assessment = assessment_match.group(1).strip() if assessment_match else "Assessment length not found"

    # Format the output as desired.
    formatted = (
        f"{product}\n\n"
        f"In this assessment there will be {description}\n\n"
        f"Job Level: {job_level}\n\n"
        f"Language is {language}\n\n"
        f"Assessment Length is Approximately {assessment} minutes maximum"
    )
    return formatted

# Streamlit app interface
st.title("Document Similarity Search")

# Use a form so that pressing Enter triggers submission
with st.form(key="search_form"):
    query = st.text_input("Enter your query:")
    submit_button = st.form_submit_button(label="Search")

if submit_button:
    if not query:
        st.error("Please enter a query!")
    else:
        results = docsearch.similarity_search(query, k=3)
        st.markdown("## The following products:")
        for i, result in enumerate(results, start=1):
            with st.expander(f"Product {i}"):
                # Pass the raw result through Gemini formatting
                formatted_text = gemini_format_product(result.page_content)
                st.markdown(formatted_text)
