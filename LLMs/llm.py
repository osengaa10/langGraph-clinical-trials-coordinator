from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

# set your API key
load_dotenv()

os.environ['GROQ_API_KEY']

GROQ_LLM = ChatGroq(
            model="llama-3.1-70b-versatile",
            
        )


model_name = "BAAI/bge-small-en-v1.5"
encode_kwargs = {'normalize_embeddings': True} # set True to compute cosine similarity
model_norm = HuggingFaceBgeEmbeddings(
    model_name=model_name,
    model_kwargs={'device': 'cpu'},
    encode_kwargs=encode_kwargs
)

embedding = model_norm