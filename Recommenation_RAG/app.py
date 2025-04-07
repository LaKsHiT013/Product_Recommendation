import streamlit as st
import requests

# Flask API endpoint
API_URL = "http://localhost:5000/query"  # Update this if your Flask server is hosted elsewhere

# Function to query the Flask API
def query_flask_api(query):
    try:
        response = requests.post(API_URL, json={"query": query})
        if response.status_code == 200:
            return response.json()
        else:
            return [{"text": f"Error: {response.status_code} - {response.text}"}]
    except Exception as e:
        return [{"text": f"Exception: {str(e)}"}]

def main():
    st.title("SHL Assessment Assistant")
    st.markdown("*Ask questions about the SHL assessment documents.*")

    if "history" not in st.session_state:
        st.session_state.history = []

    # Text input
    text_input = st.text_input("Type your question here...")

    if text_input:
        st.session_state.history.append({"role": "user", "content": text_input})
        results = query_flask_api(text_input)
        answer = "\n\n".join([r["text"] for r in results])
        st.session_state.history.append({"role": "bot", "content": answer})

    # Display chat history
    for msg in reversed(st.session_state.history):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

if __name__ == "__main__":
    main()
