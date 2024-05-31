from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
# set your API key
load_dotenv()

os.environ['GROQ_API_KEY']

GROQ_LLM = ChatGroq(
            model="llama3-70b-8192",
        )