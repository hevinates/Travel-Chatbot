# 🌍 Travel Chatbot 

This project is a Streamlit-based AI chatbot powered by Azure OpenAI, designed to provide intelligent travel guidance and document-based responses.  
It combines natural language understanding, PDF parsing, and semantic retrieval using ChromaDB to create a dynamic, context-aware assistant.

---

## ✨ Features  
- **Streamlit Interface** – Clean, interactive UI for user queries and document uploads  
- **Azure OpenAI Integration** – Uses GPT-4.1 for conversational intelligence  
- **PDF to Text Conversion** – Converts uploaded travel PDFs to searchable text using `pdf2image`  
- **Chunking and Embedding** – Splits and encodes markdown data from the *Meridian Islands* dataset  
- **ChromaDB Retrieval** – Performs semantic search over embedded data  
- **Context-Aware Responses** – Provides answers enriched with relevant document context  

---

## 🧩 Project Structure  
```
project/
│
├── project.py # Main Streamlit app
├── requirements.txt # Dependencies
├── .gitignore # Files excluded from tracking
├── all_info.txt # Merged information about Meridian Island
├── meridian-islands/ # Artificial travel dataset
```
## ⚙️ Installation

- **Clone the repository** –
  
```git clone https://github.com/hevinates/Travel-Chatbot.git```

- **Create a virtual environment** –
```
cd Travel-Chatbot
python3 -m venv .venv
source .venv/bin/activate
```

- **Install dependencies** –
  
```pip install -r requirements.txt```

- **Set up environment variables** –
Create a file named new.env in the project root and add:
```
API_KEY=your_azure_openai_key
ENDPOINT_URL=your_azure_endpoint
```
## 🗺️ Usage

To run the app:

```streamlit run project.py```
