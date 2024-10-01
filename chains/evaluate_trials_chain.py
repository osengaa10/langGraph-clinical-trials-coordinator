from langchain.prompts import PromptTemplate
from LLMs.llm import GROQ_LLM 
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser



evaluation_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a medical expert evaluating the results of a clinical trial search. Your task is to determine if a suitable clinical trial was found for the patient and, if not, what additional information is needed to find one.

    <|eot_id|><|start_header_id|>user<|end_header_id|>
    Research Information:
    {research_info}

    Determine if a suitable clinical trial was found. If a suitable trial was found, summarize it briefly. If not, clearly state that no suitable trial was found and specify what additional information is needed to find an appropriate trial.

    Format your response as follows:
    If a trial was found:
    "A suitable clinical trial was found: [Brief summary of the trial]"

    If no trial was found:
    "No suitable clinical trial found. Additional information needed: [List the required information]"
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["research_info"],
)

evaluate_trials_chain = (
    evaluation_prompt
    | GROQ_LLM
    | StrOutputParser()
)