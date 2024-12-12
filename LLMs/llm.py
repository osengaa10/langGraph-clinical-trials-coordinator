from langchain_groq import ChatGroq
from langchain_together import ChatTogether

from dotenv import load_dotenv
import os
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

# set your API key
load_dotenv()

os.environ['GROQ_API_KEY']
os.environ['TOGETHER_API_KEY']
# GROQ_LLM = ChatGroq(
#             # model="llama-3.1-70b-versatile",
#             model="llama3-8b-8192",
#         )

GROQ_LLM = ChatTogether(model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo")
CHAT_LLM = ChatTogether(model="meta-llama/Llama-3-70b-chat-hf")

model_name = "BAAI/bge-small-en-v1.5"
encode_kwargs = {'normalize_embeddings': True} # set True to compute cosine similarity
model_norm = HuggingFaceBgeEmbeddings(
    model_name=model_name,
    model_kwargs={'device': 'cpu'},
    encode_kwargs=encode_kwargs
)

embedding = model_norm