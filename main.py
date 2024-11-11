from LLMs.llm import GROQ_LLM
from graph import create_workflow
import sys
import os
from dotenv import load_dotenv

app = create_workflow(GROQ_LLM)

# run the agent
inputs = {"num_steps":0}


output = app.invoke(inputs)

print(f"output::: {output}")