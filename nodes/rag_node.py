# from chains.rag_chain import rag_chain
from utils import write_markdown_file
from langchain_core.runnables import RunnablePassthrough
from langchain.prompts import PromptTemplate
from rag import create_vector_db
from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM


def research_info_search(state):
    vectordb = create_vector_db(state['uid'])
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})

# Updated RAG Chain
    rag_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a medical expert who finds the best clinical trial for improving a patient's prognosis when provided a brief medical report. 
    Use the following pieces of retrieved context to find the most promising clinical trials for the patient. 
    If you don't find a trial that is a good fit, just say that you haven't found one.

     <|eot_id|><|start_header_id|>user<|end_header_id|>
    Medical Report: {medical_report}

    Retrieved Clinical Trials:
    {context}

    Find the most relevant clinical trials for this patient based on their medical report.
    State the expected prognosis outcome and possible risks associated.
    Ensure that you always include the NCT ID for each trial you mention as well as the contact info
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

    print("---RESEARCH INFO RAG---")
    medical_report = state["medical_report"]
    num_steps = state['num_steps']
    num_steps += 1

    # Perform RAG search using the medical report
    rag_results = rag_chain.invoke({"medical_report": medical_report})
    state["research_info"] = rag_results
    print("===RAG RESULTS===")
    print(rag_results)
    write_markdown_file([rag_results], "clinical_trials")

    return {
        "research_info": [rag_results],
        "num_steps": num_steps
    }
