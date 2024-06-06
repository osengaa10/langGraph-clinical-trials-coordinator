# from chains import research_router, rewrite_router


# def route_to_research(state):
#     """
#     Route email to web search or not.
#     Args:
#         state (dict): The current graph state
#     Returns:
#         str: Next node to call
#     """
#     print("---ROUTE TO RESEARCH---")
#     initial_prompt = state["initial_prompt"]
#     search_term = state["search_term"]
#     router = research_router.invoke({"initial_prompt": initial_prompt,"search_term":search_term })
#     print(router)
#     # print(type(router))
#     print(router['router_decision'])
#     if router['router_decision'] == 'research_info':
#         print("---ROUTE EMAIL TO RESEARCH INFO---")
#         return "research_info"
#     elif router['router_decision'] == 'draft_email':
#         print("---ROUTE EMAIL TO DRAFT EMAIL---")
#         return "draft_email"
    

# def route_to_rewrite(state):
#     print("---ROUTE TO REWRITE---")
#     initial_prompt = state["initial_prompt"]
#     search_term = state["search_term"]
#     draft_email = state["draft_email"]
#     # research_info = state["research_info"]
#     # draft_email = "Yo we can't help you, best regards Sarah"
#     router = rewrite_router.invoke({"initial_prompt": initial_prompt,
#                                      "search_term":search_term,
#                                      "draft_email":draft_email}
#                                    )
#     print(router)
#     print(router['router_decision'])
#     if router['router_decision'] == 'rewrite':
#         print("---ROUTE TO ANALYSIS - REWRITE---")
#         return "rewrite"
#     elif router['router_decision'] == 'no_rewrite':
#         print("---ROUTE EMAIL TO FINAL EMAIL---")
#         return "no_rewrite"
    
