from state import GraphState
from langgraph.graph import END, StateGraph
from nodes import prompt_distiller, trials_search, state_printer
# research_info_search, draft_email_writer, analyze_draft_email, rewrite_email, no_rewrite
# from edges import route_to_research, route_to_rewrite
# Define the workflow
workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("prompt_distiller", prompt_distiller) # categorize email
workflow.add_node("trials_search", trials_search) # categorize email
workflow.add_node("state_printer", state_printer)

workflow.set_entry_point("prompt_distiller")

workflow.add_edge("prompt_distiller", "trials_search")
workflow.add_edge("trials_search", "state_printer")
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


app = workflow.compile()



PROMPT = """HI there, \n
I am a 32 year old male with sarcoma that started in the stomach and spread to the liver.
"""

# run the agent
inputs = {"initial_prompt": PROMPT, "num_steps":0}
for output in app.stream(inputs):
    for key, value in output.items():
        print(f"Finished running: {key}:")


output = app.invoke(inputs)

print(f"output::: {output}")