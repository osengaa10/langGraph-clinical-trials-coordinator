from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM
from langchain.prompts import PromptTemplate


prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    As a top medical expert and software engineer, you will review
    a patient's prompt and distill their prompt into a single searchable word.
     
    Your response MUST BE a single word. Your single word response will be the diagnosis of the patient \
    This word will be used a search term to lookup the most relevant clinical trials to the patient
     <|eot_id|><|start_header_id|>user<|end_header_id|>
    Conduct a comprehensive analysis of the prompt provided 
    and distill their prompt into a searchable word or phrase.


            Output a single word that best describes the patient's condition.

    PATIENT PROMPT:\n\n {initial_prompt} \n\n
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["initial_prompt"],
)

prompt_distiller_chain = prompt | GROQ_LLM | StrOutputParser()