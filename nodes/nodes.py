# from utils import write_markdown_file
# from chains.chains import rag_chain, prompt_distiller_chain, trials_search_chain
# # , draft_writer_chain, draft_analysis_chain
# from utils import clinical_trials_search


# def prompt_distiller(state):
#     """take the initial prompt and return a search term"""
#     print("---DISTILLING INITIAL PROMPT---")
#     initial_prompt = state['initial_prompt']
#     num_steps = int(state['num_steps'])
#     num_steps += 1

#     search_term = prompt_distiller_chain.invoke({"initial_prompt": initial_prompt})
#     print("___SEARCH TERM___ ", search_term)
#     # save to local disk
#     write_markdown_file(search_term, "search_term")

#     return {"search_term": search_term, "num_steps":num_steps}



# def trials_search(state):
#     """make api call to search for trials"""
#     print("---FETCHING CLINICAL TRIALS---")
#     search_term = state['search_term']
#     num_steps = int(state['num_steps'])
#     num_steps += 1

#     # search_term = trials_search_chain.invoke({"search_term": search_term})
#     print("___SEARCH TERM BEFORE TRIALS SEARCH___ ", search_term)

#     clinical_trials_search(search_term)

#     # save to local disk
#     write_markdown_file(search_term, "search_term")

#     return {"search_term": search_term, "num_steps":num_steps}



# # RAG node
# def research_info_search(state):
#     print("---RESEARCH INFO RAG---")
#     initial_prompt = state["initial_prompt"]
#     medical_report = state["medical_report"]
#     num_steps = state['num_steps']
#     num_steps += 1
#     # Web search
#     questions = question_rag_chain.invoke({"initial_prompt": initial_prompt,
#                                             "medical_report": medical_report })
#     questions = questions['questions']
#     # print(questions)
#     rag_results = []
#     for question in questions:
#         print(question)
#         temp_docs = rag_chain.invoke(question)
#         print(temp_docs)
#         question_results = question + '\n\n' + temp_docs + "\n\n\n"
#         if rag_results is not None:
#             rag_results.append(question_results)
#         else:
#             rag_results = [question_results]
#     print(rag_results)
#     print(type(rag_results))
#     write_markdown_file(rag_results, "research_info")
#     write_markdown_file(questions, "rag_questions")
#     return {"research_info": rag_results,"rag_questions":questions, "num_steps":num_steps}




# # def draft_email_writer(state):
# #     print("---DRAFT EMAIL WRITER---")
# #     ## Get the state
# #     initial_prompt = state["initial_prompt"]
# #     search_term = state["search_term"]
# #     research_info = state["research_info"]
# #     num_steps = state['num_steps']
# #     num_steps += 1
# #     # Generate draft email
# #     draft_email = draft_writer_chain.invoke({"initial_prompt": initial_prompt,
# #                                      "search_term": search_term,
# #                                      "research_info":research_info})
# #     print(draft_email)
# #     # print(type(draft_email))
# #     email_draft = draft_email['email_draft']
# #     write_markdown_file(email_draft, "draft_email")
# #     return {"draft_email": email_draft, "num_steps":num_steps}



# # def analyze_draft_email(state):
# #     print("---DRAFT EMAIL ANALYZER---")
# #     ## Get the state
# #     initial_prompt = state["initial_prompt"]
# #     search_term = state["search_term"]
# #     draft_email = state["draft_email"]
# #     research_info = state["research_info"]
# #     num_steps = state['num_steps']
# #     num_steps += 1
# #     # Generate draft email
# #     draft_email_feedback = draft_analysis_chain.invoke({"initial_prompt": initial_prompt,
# #                                                 "search_term": search_term,
# #                                                 "research_info":research_info,
# #                                                 "draft_email":draft_email}
# #                                                )
# #     # print(draft_email)
# #     # print(type(draft_email))
# #     write_markdown_file(str(draft_email_feedback), "draft_email_feedback")
# #     return {"draft_email_feedback": draft_email_feedback, "num_steps":num_steps}



# # def rewrite_email(state):
# #     print("---ReWRITE EMAIL ---")
# #     ## Get the state
# #     initial_prompt = state["initial_prompt"]
# #     search_term = state["search_term"]
# #     draft_email = state["draft_email"]
# #     research_info = state["research_info"]
# #     draft_email_feedback = state["draft_email_feedback"]
# #     num_steps = state['num_steps']
# #     num_steps += 1
# #     # Generate draft email
# #     final_email = rewrite_chain.invoke({"initial_prompt": initial_prompt,
# #                                                 "search_term": search_term,
# #                                                 "research_info":research_info,
# #                                                 "draft_email":draft_email,
# #                                                 "email_analysis": draft_email_feedback}
# #                                                )

# #     write_markdown_file(str(final_email), "final_email")
# #     return {"final_email": final_email['final_email'], "num_steps":num_steps}



# # def no_rewrite(state):
# #     print("---NO REWRITE EMAIL ---")
# #     ## Get the state
# #     draft_email = state["draft_email"]
# #     num_steps = state['num_steps']
# #     num_steps += 1
# #     write_markdown_file(str(draft_email), "final_email")
# #     return {"final_email": draft_email, "num_steps":num_steps}


# def state_printer(state):
#     """print the state"""
#     print("---STATE PRINTER---")
#     print(f"Initial Prompt: {state['initial_prompt']} \n" )
#     print(f"Search Term: {state['search_term']} \n")
#     # print(f"Draft Email: {state['draft_email']} \n" )
#     # print(f"Final Email: {state['final_email']} \n" )
#     # print(f"Research Info: {state['research_info']} \n")
#     # print(f"RAG Questions: {state['rag_questions']} \n")
#     print(f"Num Steps: {state['num_steps']} \n")
#     return