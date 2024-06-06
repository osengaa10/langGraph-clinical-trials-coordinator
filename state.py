from langchain.schema import Document
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict
from typing import List

### State

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        initial_prompt: prompt
        search_term: search term
        medical_report: LLM generation
        final_medical_report: LLM generation
        research_info: list of documents
        info_needed: whether to add search info
        num_steps: number of steps
    """
    initial_prompt : str
    search_term : str
    medical_report : str
    final_medical_report : str
    research_info : List[str] # this will now be the RAG results
    info_needed : bool
    num_steps : int
    draft_email_feedback : dict
    rag_questions : List[str]