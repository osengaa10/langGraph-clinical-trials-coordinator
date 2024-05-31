from langchain.schema import Document
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict
from typing import List

### State

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        initial_email: email
        email_category: email category
        draft_email: LLM generation
        final_email: LLM generation
        research_info: list of documents
        info_needed: whether to add search info
        num_steps: number of steps
    """
    initial_email : str
    email_category : str
    draft_email : str
    final_email : str
    research_info : List[str] # this will now be the RAG results
    info_needed : bool
    num_steps : int
    draft_email_feedback : dict
    rag_questions : List[str]