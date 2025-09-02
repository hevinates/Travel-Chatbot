import streamlit as st
import pandas as pd
import os
import base64
import glob
import chromadb

from openai import AzureOpenAI
from dotenv import load_dotenv
from io import BytesIO
from pdf2image import convert_from_bytes
from dataclasses import dataclass
from chromadb.utils import embedding_functions

# ****** CHUNKING *********

exclude = ['./CLAUDE.md','./progress-tracker.md','./project-description.md']
list_of_files = glob.glob('meridian-islands/**/*.md', recursive=True) 
filtered_list = []
for a in list_of_files:
    if a not in exclude:
        filtered_list.append(a)

filtered_list = sorted(filtered_list)

@dataclass
class Chunk:
        text: str
        chunk_id: int
        start_pos: int
        end_pos: int
        word_count: int
        origin_file: str

class Chunker:
    def __init__(self,chunk_size: int,overlap: int):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.id = 0
        
    def chunk(self, given_list: str) -> list[Chunk]:

        with open(given_list, "r", encoding="utf-8") as f:
            converted_text = f.read() 
        #print(given_list)
        chunk_size = self.chunk_size
        overlap = self.overlap
        chunks = []
        
        words = converted_text.split()  

        for start in (range(0, len(words), chunk_size)):
            if start == 0:
                adj_start = start
            else:
                adj_start = max(0, start - overlap)

            end = min(adj_start+chunk_size, len(words))
            chunk = words[adj_start:end]

            chunks.append(
                Chunk(
                    text=chunk,
                    chunk_id=self.id,
                    start_pos=adj_start,
                    end_pos=end-1,
                    word_count=len(chunk),
                    origin_file=given_list
                )
            )
            self.id += 1
            
        return chunks
    
chunker: Chunker = Chunker(150,25)

all_chunks = []
for a in filtered_list:
    chunks: list = chunker.chunk(a)
    all_chunks.extend(chunks)

# ******** OPENAI *********  

load_dotenv("new.env")

endpoint = os.getenv("ENDPOINT_URL")
model_name = "gpt-4.1"

subscription_key = os.getenv("API_KEY")
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)


chroma_client = chromadb.PersistentClient(path="./chroma_db")
default_ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(
    name="meridian_travel_docs",
    embedding_function=default_ef
)

chunk_ids = []
docs = []
metas = []
for chunk in all_chunks:
    chunk_ids.append(str(chunk.chunk_id))

    txt = " ".join(chunk.text)   
    docs.append(txt)

    metas.append({
        "origin_file": chunk.origin_file,
        "start_pos": chunk.start_pos,
        "end_pos": chunk.end_pos
    })
collection.add(
    ids=chunk_ids,
    documents=docs,
    metadatas=metas
)

    
st.title('chat-gpt')

st.session_state["openai_model"] = "gpt-4.1"
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4.1"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Say something"):

    results = collection.query(query_texts=prompt, n_results=3)
    
    user_msg = f"{prompt}\nhere is the needed data: \n{collection}"
   
    st.session_state.messages.append({"role": "user", "content": user_msg})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": "system", "content": "Start giving advices when you are asked."
                "Use the needed data if user asks about meridian islands."
                "Do not mention meridian islands file."
                "You are a helpful and experienced tourist guide when you are asked about travelling. "
                "Give 4-5 places."
                "Give most important 3 tips and the end below 'Tips' title."
                "Give the most common phrases in that place's official language that can a tourist might need."
                "Also give languages that are spoken in that place."
                }
            ] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})


