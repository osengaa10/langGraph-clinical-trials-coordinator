# from state import GraphState
from langgraph.graph import END, StateGraph
from nodes.prompt_distiller_node import prompt_distiller 
from nodes.trials_search_node import trials_search 
from nodes.state_printer_node import state_printer
from nodes.consultant_node import consultant
# research_info_search, draft_email_writer, analyze_draft_email, rewrite_email, no_rewrite
# from edges import route_to_research, route_to_rewrite
# Define the workflow



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
        chat_history: LLM and Human convo
        final_medical_report: LLM generation
        research_info: list of documents
        info_needed: whether to add search info
        num_steps: number of steps
    """
    initial_prompt : str
    search_term : str
    chat_history: str
    medical_report : str
    final_medical_report : str
    research_info : List[str] # this will now be the RAG results
    info_needed : bool
    num_steps : int
    draft_email_feedback : dict
    rag_questions : List[str]


# Define the nodes
def create_workflow(llm):
    workflow = StateGraph(GraphState)

    # add nodes
    workflow.add_node("prompt_distiller", prompt_distiller) # categorize email
    workflow.add_node("trials_search", trials_search) # categorize email
    workflow.add_node("consultant", consultant)
    workflow.add_node("state_printer", state_printer)


    workflow.set_entry_point("prompt_distiller")

    workflow.add_edge("prompt_distiller", "trials_search")
    workflow.add_edge("trials_search", "consultant")
    workflow.add_edge("consultant", "state_printer")
    workflow.add_edge("state_printer", END)




    # workflow.add_node("research_info_search", research_info_search) # web search
    # workflow.add_node("state_printer", state_printer)
    # workflow.add_node("draft_email_writer", draft_email_writer)
    # workflow.add_node("analyze_draft_email", analyze_draft_email)
    # workflow.add_node("rewrite_email", rewrite_email)
    # workflow.add_node("no_rewrite", no_rewrite)


    # workflow.set_entry_point("prompt_distiller")

    # # workflow.add_conditional_edges(
    # #     "categorize_email",
    # #     route_to_research,
    # #     {
    # #         "research_info": "research_info_search",
    # #         "draft_email": "draft_email_writer",
    # #     },
    # # )
    # workflow.add_edge("prompt_distiller", "trials_search")
    # workflow.add_edge("research_info_search", "draft_email_writer")
    # workflow.add_conditional_edges(
    #     "draft_email_writer",
    #     route_to_rewrite,
    #     {
    #         "rewrite": "analyze_draft_email",
    #         "no_rewrite": "no_rewrite",
    #     },
    # )
    # workflow.add_edge("analyze_draft_email", "rewrite_email")
    # workflow.add_edge("no_rewrite", "state_printer")
    # workflow.add_edge("rewrite_email", "state_printer")
    # workflow.add_edge("state_printer", END)

    return workflow.compile()


