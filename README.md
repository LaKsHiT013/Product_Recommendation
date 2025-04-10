# Product_Recommendation

The SHL Assessment Assistant is a retrieval-augmented system designed to provide accurate and relevant recommendations for SHL assessments based on user queries. The project comprises a Flask API backend for processing queries and a Streamlit frontend for interactive user engagement. The system leverages web scraping, data embedding, and a vector database (Pinecone) for fast similarity searches.

---

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Data Collection & Processing](#data-collection--processing)
- [API Endpoints](#api-endpoints)
- [Dynamic Threshold Adjustment](#dynamic-threshold-adjustment)
- [Usage](#usage)

---

## Overview

The goal of this project was to build an assistant that can answer queries related to SHL assessment documents. The system retrieves relevant assessments from a pre-scraped dataset based on a natural language query. After processing the query through an embedding model, the vector database is searched to return the most semantically similar assessments. The results include key details such as URL, description, duration, support options, and test type.

---

## Architecture

1. **Data Collection:**  
   - I broke the web scraping process into sub-tasks. First, I observed that each table page on the SHL website had a unique URL with only numerical components changing. I compiled these URLs into a `.txt` file. Using Python's `requests` and `BeautifulSoup` (with Selenium for dynamic content), I scraped the data from both the primary and nested links.
   
2. **Data Embedding:**  
   - After extracting the required data, I observed that the assessment descriptions contained the core information. To efficiently retrieve relevant assessments, I generated embeddings only for the description field. This streamlined the storage process in the vector database and improved retrieval accuracy.

3. **Vector Database & Retrieval:**  
   - The embeddings are stored in Pinecone, a vector database designed for fast similarity searches. When a query is submitted, it is embedded and compared against the stored vectors to find the most similar assessment descriptions.
   
4. **Dynamic Threshold:**  
   - A dynamic threshold mechanism was implemented for similarity searches. Initially set to 0.7, if the number of retrieved results is less than three, the threshold is decreased by 0.05 until at least three relevant suggestions are obtained.

5. **Frontend Integration:**  
   - A Streamlit frontend provides an interactive interface that communicates with the Flask API. Users can enter queries and view the recommended assessments directly.

---

## Data Collection & Processing

Data was collected by splitting the web scraping process into several steps:
- **URL Pattern Identification:** I noticed that the table pages had systematic URL patterns (only numbers changed). I saved these URLs in a `.txt` file.
- **Table Scraping:** I used `requests` and `BeautifulSoup` to scrape the tables from these pages.
- **Nested Data Extraction:** Each table contained links to additional pages with more detailed information. I automated the process to click through these links and capture the nested data.
- **Dynamic Content Handling:** Selenium was integrated to handle JavaScript-rendered content, ensuring complete data extraction.

---

## API Endpoints

### 1. Health Check
- **Endpoint:** `/health`
- **Method:** `GET`
- **Description:** Returns the health status of the API.
- **Response Example:**
  ```json
  {
    "status": "healthy"
  }
  ```
### 2. Recommend
- **Endpoint:** `/recommend`
- **Method:** `POST`
- **Description:** Accepts a job description or natural language query and returns up to 10 recommended assessments that meet a dynamic similarity threshold.
- **Request Example:**
  ```json
  {
    "query": "Data Scientist Intern"
  }
  ```
- **Response Example:**
  ```json
     {
     "recommended_assessments": [
       {
         "url": "https://www.shl.com/solutions/products/product-catalog/view/net-mvvm-new/",
         "adaptive_support": "No",
         "description": "Multi-choice test that measures the conceptual knowledge on ...",
         "duration": 45,
         "remote_support": "Yes",
         "test_type": ["Stimulations"]
       },
       {
         "url": "https://www.shl.com/solutions/products/product-catalog/view/another-assessment/",
         "adaptive_support": "Yes",
         "description": "Another description here ...",
         "duration": 60,
         "remote_support": "No",
         "test_type": ["Knowledge & Skills"]
       }
     ]
   }
```
---
## Dynamic Threshold Adjustment

The similarity threshold for retrieving recommendations is adaptive. It is initially set to 0.7. If fewer than three recommendations are returned, the threshold is lowered by 0.05 increments until at least three results are achieved. This ensures users receive a sufficient number of relevant recommendations.

---

## Usage

**For API Testing:**  
Use tools like Postman to send requests to the API endpoints on the Render-hosted URL.

**For End-User Interaction:**  
Access the Streamlit application via its public Render URL. Enter your query in the provided text field and click "Search" to view recommended assessments.
