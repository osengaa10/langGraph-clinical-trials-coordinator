from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM  # You might need to change this import depending on the LLM you're using
from langchain.prompts import PromptTemplate

trials_search_prompt = PromptTemplate(
    template="""<s>[INST] <<SYS>>
As a top medical expert and software engineer, you will use the key words
from the Prompt Distiller to fetch a list of all relevant clinical trials.
<</SYS>>

Use the following search term to find and list relevant clinical trials:

SEARCH_TERM: {search_term}

Provide a comprehensive list of clinical trials that are relevant to this search term. Include brief descriptions and any key eligibility criteria for each trial.
[/INST]
""",
    input_variables=["search_term"],
)

trials_search_chain = trials_search_prompt | GROQ_LLM | StrOutputParser()
