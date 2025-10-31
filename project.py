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


# *************************
# ****** CHUNKING *********
# *************************


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


# *************************
# ******* CHROMA DB *******
# *************************


st.title('chat-gpt')
load_dotenv("new.env")
client = AzureOpenAI(api_version="2024-12-01-preview",
                     api_key=os.getenv("API_KEY"),
                       azure_endpoint=os.getenv("ENDPOINT_URL"))

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

if collection.count() == 0:
    collection.add(
        ids=chunk_ids,
        documents=docs,
        metadatas=metas
    )


# *************************
# ***** STREAMLIT APP *****
# *************************


# 1) STREAMLIT PDF CONVERT


all_output_text = []

uploaded = st.file_uploader("Upload PDF", type=["pdf"])
if uploaded:
    # pdf to image
    pdf_bytes = uploaded.read()
    pages = convert_from_bytes(pdf_bytes, fmt="png")

    for page in pages:  # image to base64
        buf = BytesIO()
        page.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        content = [
            {"type": "text", "text": "Transcribe exactly."
            " Preserve line breaks."
            " No summary."
            " Just output text."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
        ]

        resp = client.chat.completions.create(
            model="gpt-4.1",   
            messages=[{"role": "user", "content": content}]
        )

        all_output_text.append(resp.choices[0].message.content.strip())


# 2) STREAMLIT CHATBOT

st.session_state["openai_model"] = "gpt-4.1"
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4.1"
st.write("Using deployment:", st.session_state["openai_model"])


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Say something"):
    
    user_msg = f"{prompt}\n\nHere is the uploaded file, use this if uploaded, else nothing to mention:\n{all_output_text}"

    # important
    results = collection.query(query_texts=[user_msg], n_results=3)
    context = "\n\n".join(results["documents"][0])

   
    st.session_state.messages.append({"role": "user", "content": user_msg})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": "system", "content": "Start giving advices when you are asked."
                "Do not talk about travelling without asking."
                "You are a helpful and experienced tourist guide when you are asked about travelling. "
                "Give 8-10 places."
                "List it simply but also make it eye-catching."
                "Consider the length of trip such as day trip or more than one day. "
                "The places and the distance between them should be sensible."
                "Suggest 2-3 options for accomodation, some budge-friendly options and some safer places in that city."
                "Show the transportation to that destination from the previous place and the transportation time."
                "Try to find most sensible and effective travel time to sort places."
                "Give the time that will be spent there approximately."
                "Give most important 3 tips and the end below 'Tips' title."
                "Give the common greetings in that place's official language that can a tourist might need."
                "Use this context if user mentions 'meridian islands' or 'meridian island' " + context
                }
            ] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})

