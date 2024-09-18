from LLMs.llm import GROQ_LLM
from graph import create_workflow
import sys
import os
from dotenv import load_dotenv

app = create_workflow(GROQ_LLM)


PROMPT = """
I am a 49 year old male with bladder cancer.
"""

# run the agent
inputs = {"initial_prompt": PROMPT, "num_steps":0}
# for output in app.stream(inputs):
#     for key, value in output.items():
#         print(f"Finished running: {key}:")


output = app.invoke(inputs)

print(f"output::: {output}")