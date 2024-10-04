from chains.rag_chain import rag_chain
from utils import write_markdown_file


def research_info_search(state):
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
