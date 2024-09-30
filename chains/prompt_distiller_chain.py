from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    As a top medical expert and software engineer, you will review
    a patient's prompt and distill their prompt into a searchable term or phrase.
     
    Your response should be a concise term or short phrase (1-3 words) that best describes the patient's condition. \
    This term or phrase will be used as a search term to lookup the most relevant clinical trials for the patient.

    Existing search terms: {existing_terms}

    Your new search term must be different from the existing terms.
     <|eot_id|><|start_header_id|>user<|end_header_id|>
    Conduct a comprehensive analysis of the prompt provided 
    and distill their prompt into a searchable term or short phrase.

    Output a concise term or short phrase (1-3 words) that best describes the patient's condition.
    Ensure your output is different from the existing search terms.

    PATIENT PROMPT:\n\n {medical_report} \n\n
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["medical_report", "existing_terms"],
)

prompt_distiller_chain = prompt | GROQ_LLM | StrOutputParser()