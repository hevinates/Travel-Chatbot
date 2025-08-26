import streamlit as st
import pandas as pd
import random

st.title('ChatBot')

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])    

if prompt := st.chat_input("Say something?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

responses = ["How can I help you today?", "Sorry, I can not answer that.", "I am not sure." ]
    # Display assistant response in chat message container

response = random.choice(responses)


with st.chat_message("assistant"):
    st.markdown(response)

    # Add assistant response to chat history
st.session_state.messages.append({"role": "assistant", "content": response})