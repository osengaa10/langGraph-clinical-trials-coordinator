# from langchain_core.prompts import ChatPromptTemplate
# from langchain.prompts import PromptTemplate
# from langchain_core.runnables import RunnablePassthrough
# from langchain.vectorstores import Chroma
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.output_parsers import JsonOutputParser
# from LLMs.llm import GROQ_LLM
# from rag import vectordb


# vectordb = Chroma(embedding_function=configs.embedding, persist_directory=persist_directory)

# retriever = vectordb.as_retriever(search_kwargs={"k": 5})


# #RAG Chain
# rag_prompt = PromptTemplate(
#     template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
#     You are a medical expert who finds the best fitting clinical trial for a patient. Use the following pieces of retrieved context to find the most promising clinical for the patient. If you don't find a trial that is a good fit, just say that you haven't found one.\n

#      <|eot_id|><|start_header_id|>user<|end_header_id|>
#     QUESTION: {question} \n
#     CONTEXT: {context} \n
#     Answer:
#     <|eot_id|>
#     <|start_header_id|>assistant<|end_header_id|>
#     """,
#     input_variables=["question","context"],
# )
# rag_prompt_chain = rag_prompt | GROQ_LLM | StrOutputParser()
# QUESTION = """What is the best clinical trial for a 32 year old male with sarcoma that started in the stomach and spread to the liver?"""
# CONTEXT = retriever.invoke(QUESTION)
# result = rag_prompt_chain.invoke({"question": QUESTION, "context":CONTEXT})

# rag_chain = (
#     {"context": retriever , "question": RunnablePassthrough()}
#     | rag_prompt
#     | GROQ_LLM
#     | StrOutputParser()
# )


# #Categorize EMAIL
# # (step 1) Prompt Distiller
# prompt = PromptTemplate(
#     template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
#     a top medical expert and software engineer, you will review
#     a patient's prompt and distill their prompt into a single searchable word.
     
#     Your response MUST BE a single word. Your single word response will be the diagnosis of the patient \
#     This word will be used a search term to lookup the most relevant clinical trials to the
#      <|eot_id|><|start_header_id|>user<|end_header_id|>
#     Conduct a comprehensive analysis of the prompt provided 
#     and distill their prompt into a searchable word or phrase.


#             Output a single word that best describes the patient's condition.

#     PATIENT PROMPT:\n\n {initial_prompt} \n\n
#     <|eot_id|>
#     <|start_header_id|>assistant<|end_header_id|>
#     """,
#     input_variables=["initial_prompt"],
# )

# prompt_distiller_chain = prompt | GROQ_LLM | StrOutputParser()
# # search_term_generator = prompt | GROQ_LLM | StrOutputParser()

# PROMPT = """I am a 32 year old male with sarcoma that started in the stomach and spread to the liver. 
# What is the best clinical trial for me?
# """

# result = prompt_distiller_chain.invoke({"initial_prompt": PROMPT})

# print(f"prompt_distiller_chain invoked::: {result}")



# ## Research Router
# # (step 2) Trials Search
# trials_search_prompt = PromptTemplate(
#     template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
#     As a top medical expert and software engineer, you will use the key words
#     from the Prompt Distiller to fetch a list of all relevant clinical trials. \n

#     <|eot_id|><|start_header_id|>user<|end_header_id|>
#     SEARCH_TERM: {search_term} \n
#     <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
#     input_variables=["search_term"],
# )

# trials_search_chain = trials_search_prompt | GROQ_LLM | StrOutputParser()

# search_term = 'sarcoma'
# print(":::trials_search_chain invoked:::")
# print(trials_search_chain.invoke({"search_term":search_term}))
# print(":::trials_search_chain invoked:::")



# # ## Write Draft Email
# # # (step 3) Patient Consultant
# # report_writer_prompt = PromptTemplate(
# #     template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# #     You are the Patient Consultant Agent, take the INITIAL_PROMPT below \
# #     from a human and converse with them asking any questions needed to generate an informative medical report for the Clinical Trials Coordinator.
            
# #             You are the medical expert, so you can ask any questions you need to get the best information for the patient. \
# #             Your medical report should be comprehensive and contain enough information that the Clinical Trials Coordinator shoud need 
# #             to determine eligibility, ineligibility and the best fit clinical trials for the patient. \

# #             Return the report as JSON with a single key 'medical_report' and no premable or explaination.

# #     <|eot_id|><|start_header_id|>user<|end_header_id|>
# #     INITIAL_PROMPT: {initial_prompt} \n

# #     <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
# #     # input_variables=["initial_prompt", "medical_report"],
# #     input_variables=["initial_prompt"],

# # )
# # # add below initial_prompt to the input_variables and prompt template
# # # MEDICAL_REPORT: {medical_report} \n

# # report_writer_chain = report_writer_prompt | GROQ_LLM | JsonOutputParser()

# # # search_term = 'customer_feedback'
# # research_info = None

# # print(":::report_writer_chain invoked:::")
# # print(report_writer_chain.invoke({"initial_prompt": PROMPT}))
# # print(":::report_writer_chain invoked:::")



# # ## RAG QUESTIONS
# # # (step 4) RAG Questions
# # search_rag_prompt = PromptTemplate(
# #     template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# #     You are a master at working out the best questions to ask our knowledge agent to get the best fit clinical trials for the patient.

# #     given the MEDICAL_REPORT and INITIAL_PROMPT, Work out the best questions that will find the best clinical trials \
# #     that the patient can participate in. Remember structure the questions such that they contain 
# #     the most amount of relevant medical information in order to determine eligibility. 
# #     Write the questions to our knowledge system not to the patient.

# #     Return a JSON with a single key 'questions' with no more than 3 strings of and no premable or explanation.

# #     <|eot_id|><|start_header_id|>user<|end_header_id|>
# #     INITIAL_PROMPT: {initial_prompt} \n
# #     MEDICAL_REPORT: {medical_report} \n
# #     <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
# #     input_variables=["initial_prompt", "medical_report"],
# # )

# # question_rag_chain = search_rag_prompt | GROQ_LLM | JsonOutputParser()

# # medical_report = '32 year old male with stage 3 soft-tissue sarcoma. ECOG performance status of 2. Treatment consisted of: PK1 inhibitors that were ineffective.'
# # research_info = None

# # print(f"question_rag_chain invoked:::", question_rag_chain.invoke({"initial_prompt": PROMPT, "medical_report":medical_report}))




# # # ## Rewrite Router
# # # rewrite_router_prompt = PromptTemplate(
# # #     template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# # #     You are an expert at evaluating the emails that are draft emails for the customer and deciding if they
# # #     need to be rewritten to be better. \n

# # #     Use the following criteria to decide if the DRAFT_EMAIL needs to be rewritten: \n\n

# # #     If the INITIAL_PROMPT only requires a simple response which the DRAFT_EMAIL contains then it doesn't need to be rewritten.
# # #     If the DRAFT_EMAIL addresses all the concerns of the INITIAL_PROMPT then it doesn't need to be rewritten.
# # #     If the DRAFT_EMAIL is missing information that the INITIAL_PROMPT requires then it needs to be rewritten.

# # #     Give a binary choice 'rewrite' (for needs to be rewritten) or 'no_rewrite' (for doesn't need to be rewritten) based on the DRAFT_EMAIL and the criteria.
# # #     Return the a JSON with a single key 'router_decision' and no premable or explaination. \
# # #     <|eot_id|><|start_header_id|>user<|end_header_id|>
# # #     INITIAL_PROMPT: {initial_prompt} \n
# # #     SEARCH_TERM: {search_term} \n
# # #     DRAFT_EMAIL: {draft_email} \n
# # #     <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
# # #     input_variables=["initial_prompt","search_term","draft_email"],
# # # )

# # # rewrite_router = rewrite_router_prompt | GROQ_LLM | JsonOutputParser()

# # # search_term = 'customer_feedback'
# # # draft_email = "Yo we can't help you, best regards Sarah"

# # # print(rewrite_router.invoke({"initial_prompt": EMAIL, "search_term":search_term, "draft_email":draft_email}))



# # ## Draft Email Analysis
# # clinical_trials_coordinator_prompt = PromptTemplate(
# #     template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# #     As a renowned Medical Expert you have an exceptional ability to determine the most \
# #     promising clinical trials when provided with a description of the patient's health issue. \
# #     Your ability to match patients with clinical trials has saved many lives.\
# #     Use the following pieces of retrieved context to find the best clinical trials for the patient. \
# #     Your reviews are always comprehensive and thorough since you know lives depend on you. \

# #     Check the RESEARCH_INFO for the best fitting clinical trial for the patient based off of the MEDICAL_REPORT. \
# #     Review the eligibility criteria and ensure the patient is a good fit for the trial. \
   
# #     You never make up or add information that hasn't been provided by the research_info or in the medical_report.

# #     Return the analysis a JSON with a single key 'trial_analysis' and no premable or explaination.

# #     <|eot_id|><|start_header_id|>user<|end_header_id|>
# #     INITIAL_PROMPT: {initial_prompt} \n\n
# #     MEDICAL_REPORT: {medical_report} \n\n
# #     RESEARCH_INFO: {research_info} \n\n
# #     <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
# #     input_variables=["initial_prompt","medical_report","research_info"],
# # )

# # clinical_trials_coordinator_chain = clinical_trials_coordinator_prompt | GROQ_LLM | JsonOutputParser()

# # search_term = 'customer_feedback'
# # research_info = None
# # draft_email = "Yo we can't help you, best regards Sarah"

# # trial_analysis = clinical_trials_coordinator_prompt.invoke({"initial_prompt": PROMPT,
# #                                  "medical_report":medical_report,
# #                                  "research_info":research_info})

# # print(trial_analysis)



# # # Rewrite Email with Analysis
# # rewrite_email_prompt = PromptTemplate(
# #     template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# #     You are the Final Email Agent read the email analysis below from the QC Agent \
# #     and use it to rewrite and improve the draft_email to create a final email.


# #     You never make up or add information that hasn't been provided by the research_info or in the initial_prompt.

# #     Return the final email as VALID JSON with a single key 'final_email' which is a string and no premable or explaination.


# #     <|eot_id|><|start_header_id|>user<|end_header_id|>
# #     SEARCH_TERM: {search_term} \n\n
# #     RESEARCH_INFO: {research_info} \n\n
# #     DRAFT_EMAIL: {draft_email} \n\n
# #     DRAFT_EMAIL_FEEDBACK: {email_analysis} \n\n
# #     <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
# #     input_variables=["initial_prompt",
# #                      "search_term",
# #                      "research_info",
# #                      "email_analysis",
# #                      "draft_email",
# #                      ],
# # )

# # rewrite_chain = rewrite_email_prompt | GROQ_LLM | JsonOutputParser()

# # search_term = 'sarcoma'
# # research_info = None
# # # draft_email = "Yo we can't help you, best regards Sarah"

# # final_email = rewrite_chain.invoke({"initial_prompt": PROMPT,
# #                                  "medical_report":medical_report,
# #                                  "research_info":research_info,
# #                                 "trial_analysis":trial_analysis})

# # # final_email['final_email']