# from state import GraphState
from langgraph.graph import END, StateGraph
from nodes.prompt_distiller_node import prompt_distiller 
from nodes.trials_search_node import trials_search 
from nodes.state_printer_node import state_printer
from nodes.consultant_node import consultant
from nodes.rag_node import research_info_search
from nodes.evaluate_trials_node import evaluate_research_info
from langchain.schema import Document
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict
from typing import List

### State

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        medical_report: LLM generation
        search_term: search term
        chat_history: LLM and Human convo
        final_medical_report: LLM generation
        research_info: list of documents
        follow_up: whether to add search info
        num_steps: number of steps
        next_step: str 
    """
    medical_report : str
    search_term : List[str]
    chat_history: str
    final_medical_report : str
    research_info : List[str] # this will now be the RAG results
    follow_up : str
    num_steps : int
    next_step: str 
    draft_email_feedback : dict
    rag_questions : List[str]


# Define the nodes
def create_workflow(llm):
    workflow = StateGraph(GraphState)

    # add nodes
    workflow.add_node("consultant", consultant)
    workflow.add_node("prompt_distiller", prompt_distiller) 
    workflow.add_node("trials_search", trials_search) 
    workflow.add_node("research_info_search", research_info_search)
    workflow.add_node("evaluate_research_info", evaluate_research_info)
    workflow.add_node("state_printer", state_printer)


    workflow.set_entry_point("consultant")

    workflow.add_edge("consultant", "prompt_distiller")
    workflow.add_edge("prompt_distiller", "trials_search")
    workflow.add_edge("trials_search", "research_info_search")
    workflow.add_edge("research_info_search", "evaluate_research_info")

    workflow.add_conditional_edges(
        "evaluate_research_info",
        lambda x: x["next_step"],
        {
            "state_printer": "state_printer",
            "consultant": "consultant"
        }

    )

    workflow.add_edge("state_printer", END)


    return workflow.compile()


