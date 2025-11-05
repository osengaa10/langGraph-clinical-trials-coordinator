from langchain_groq import ChatGroq
from langchain_together import ChatTogether
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

# set your API key
load_dotenv()

os.environ['GROQ_API_KEY']
os.environ['TOGETHER_API_KEY']
deepseek_api_key = os.environ['OPENROUTER_API_KEY']

# Multi-LLM Architecture for Clinical Trials Coordinator
# - CONVERSATIONAL_LLM: Patient interaction and general tasks (Llama-3.3-70B)
# - REASONING_LLM: Complex medical reasoning and trial evaluation (DeepSeek-R1)

# Conversational LLM for patient interaction, report generation, and term extraction
CONVERSATIONAL_LLM = ChatTogether(model="meta-llama/Llama-3.3-70B-Instruct-Turbo")

# Reasoning LLM for complex medical analysis and trial evaluation
# max_tokens set to 1500 to ensure inputs + outputs stay within 8K context limit
REASONING_LLM = ChatTogether(
    model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
    max_tokens=1500
)

# Backward compatibility - points to reasoning model
GROQ_LLM = REASONING_LLM

model_name = "BAAI/bge-small-en-v1.5"
encode_kwargs = {'normalize_embeddings': True} # set True to compute cosine similarity
model_norm = HuggingFaceBgeEmbeddings(
    model_name=model_name,
    model_kwargs={'device': 'cpu'},
    encode_kwargs=encode_kwargs
)

embedding = model_norm