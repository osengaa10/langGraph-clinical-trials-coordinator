from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from rag import vectordb
from utils import write_markdown_file

# Update the retriever to use the medical report
retriever = vectordb.as_retriever(search_kwargs={"k": 5})

# Updated RAG Chain
rag_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a medical expert who finds the best fitting clinical trial for a patient when provided a brief medical report. 
    Use the following pieces of retrieved context to find the most promising clinical trials for the patient. 
    If you don't find a trial that is a good fit, just say that you haven't found one.

     <|eot_id|><|start_header_id|>user<|end_header_id|>
    Medical Report: {medical_report}

    Retrieved Clinical Trials:
    {context}

    Find the most relevant clinical trials for this patient based on their medical report.
    State the expected outcome and possible risks associated.
    Ensure that you always include the NCT ID for each trial you mention
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["medical_report", "context"],
)

rag_chain = (
    {
        "context": lambda x: retriever.get_relevant_documents(x["medical_report"]),
        "medical_report": RunnablePassthrough()
    }
    | rag_prompt
    | GROQ_LLM
    | StrOutputParser()
)
