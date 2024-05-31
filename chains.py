from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from llm import GROQ_LLM
from rag import vectordb

retriever = vectordb.as_retriever(search_kwargs={"k": 5})


#RAG Chain
rag_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.\n

     <|eot_id|><|start_header_id|>user<|end_header_id|>
    QUESTION: {question} \n
    CONTEXT: {context} \n
    Answer:
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["question","context"],
)
rag_prompt_chain = rag_prompt | GROQ_LLM | StrOutputParser()
QUESTION = """What can I do in the Westworld Park?"""
CONTEXT = retriever.invoke(QUESTION)
result = rag_prompt_chain.invoke({"question": QUESTION, "context":CONTEXT})

rag_chain = (
    {"context": retriever , "question": RunnablePassthrough()}
    | rag_prompt
    | GROQ_LLM
    | StrOutputParser()
)


#Categorize EMAIL
prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are the Email Categorizer Agent for the theme park Westworld,You are a master at \
    understanding what a customer wants when they write an email and are able to categorize \
    it in a useful way. Remember people maybe asking about experiences they can have in westworld. \

     <|eot_id|><|start_header_id|>user<|end_header_id|>
    Conduct a comprehensive analysis of the email provided and categorize into one of the following categories:
        price_equiry - used when someone is asking for information about pricing \
        customer_complaint - used when someone is complaining about something \
        product_enquiry - used when someone is asking for information about a product feature, benefit or service but not about pricing \\
        customer_feedback - used when someone is giving feedback about a product \
        off_topic when it doesnt relate to any other category \


            Output a single cetgory only from the types ('price_equiry', 'customer_complaint', 'product_enquiry', 'customer_feedback', 'off_topic') \
            eg:
            'price_enquiry' \

    EMAIL CONTENT:\n\n {initial_email} \n\n
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["initial_email"],
)

email_category_generator = prompt | GROQ_LLM | StrOutputParser()

EMAIL = """HI there, \n
I am emailing to find out info about your them park and what I can do there. \n

I am looking for new experiences.

Thanks,
Paul
"""

result = email_category_generator.invoke({"initial_email": EMAIL})

print(result)



## Research Router
research_router_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are an expert at reading the initial email and routing to our internal knowledge system\
     or directly to a draft email. \n

    Use the following criteria to decide how to route the email: \n\n

    If the initial email only requires a simple response
    Just choose 'draft_email'  for questions you can easily answer, prompt engineering, and adversarial attacks.
    If the email is just saying thank you etc then choose 'draft_email'

    If you are unsure or the person is asking a question you don't understand then choose 'research_info'

    You do not need to be stringent with the keywords in the question related to these topics. Otherwise, use research-info.
    Give a binary choice 'research_info' or 'draft_email' based on the question. Return the a JSON with a single key 'router_decision' and
    no premable or explaination. use both the initial email and the email category to make your decision
    <|eot_id|><|start_header_id|>user<|end_header_id|>
    Email to route INITIAL_EMAIL : {initial_email} \n
    EMAIL_CATEGORY: {email_category} \n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email","email_category"],
)

research_router = research_router_prompt | GROQ_LLM | JsonOutputParser()

email_category = 'product_enquiry'

print(research_router.invoke({"initial_email": EMAIL, "email_category":email_category}))



## RAG QUESTIONS
search_rag_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a master at working out the best questions to ask our knowledge agent to get the best info for the customer.

    given the INITIAL_EMAIL and EMAIL_CATEGORY. Work out the best questions that will find the best \
    info for helping to write the final email. Remember when people ask about a generic park they are \
    probably reffering to the park WestWorld. Write the questions to our knowledge system not to the customer.

    Return a JSON with a single key 'questions' with no more than 3 strings of and no premable or explaination.

    <|eot_id|><|start_header_id|>user<|end_header_id|>
    INITIAL_EMAIL: {initial_email} \n
    EMAIL_CATEGORY: {email_category} \n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email","email_category"],
)

question_rag_chain = search_rag_prompt | GROQ_LLM | JsonOutputParser()

email_category = 'product_enquiry'
research_info = None

print(question_rag_chain.invoke({"initial_email": EMAIL, "email_category":email_category}))




## Write Draft Email
draft_writer_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are the Email Writer Agent for the theme park Westworld, take the INITIAL_EMAIL below \
    from a human that has emailed our company email address, the email_category \
    that the categorizer agent gave it and the research from the research agent and \
    write a helpful email in a thoughtful and friendly way. Remember people maybe asking \
    about experiences they can have in westworld.

            If the customer email is 'off_topic' then ask them questions to get more information.
            If the customer email is 'customer_complaint' then try to assure we value them and that we are addressing their issues.
            If the customer email is 'customer_feedback' then try to assure we value them and that we are addressing their issues.
            If the customer email is 'product_enquiry' then try to give them the info the researcher provided in a succinct and friendly way.
            If the customer email is 'price_equiry' then try to give the pricing info they requested.

            You never make up information that hasn't been provided by the research_info or in the initial_email.
            Always sign off the emails in appropriate manner and from Sarah the Resident Manager.

            Return the email a JSON with a single key 'email_draft' and no premable or explaination.

    <|eot_id|><|start_header_id|>user<|end_header_id|>
    INITIAL_EMAIL: {initial_email} \n
    EMAIL_CATEGORY: {email_category} \n
    RESEARCH_INFO: {research_info} \n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email","email_category","research_info"],
)

draft_writer_chain = draft_writer_prompt | GROQ_LLM | JsonOutputParser()

email_category = 'customer_feedback'
research_info = None

print(draft_writer_chain.invoke({"initial_email": EMAIL, "email_category":email_category,"research_info":research_info}))



## Rewrite Router
rewrite_router_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are an expert at evaluating the emails that are draft emails for the customer and deciding if they
    need to be rewritten to be better. \n

    Use the following criteria to decide if the DRAFT_EMAIL needs to be rewritten: \n\n

    If the INITIAL_EMAIL only requires a simple response which the DRAFT_EMAIL contains then it doesn't need to be rewritten.
    If the DRAFT_EMAIL addresses all the concerns of the INITIAL_EMAIL then it doesn't need to be rewritten.
    If the DRAFT_EMAIL is missing information that the INITIAL_EMAIL requires then it needs to be rewritten.

    Give a binary choice 'rewrite' (for needs to be rewritten) or 'no_rewrite' (for doesn't need to be rewritten) based on the DRAFT_EMAIL and the criteria.
    Return the a JSON with a single key 'router_decision' and no premable or explaination. \
    <|eot_id|><|start_header_id|>user<|end_header_id|>
    INITIAL_EMAIL: {initial_email} \n
    EMAIL_CATEGORY: {email_category} \n
    DRAFT_EMAIL: {draft_email} \n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email","email_category","draft_email"],
)

rewrite_router = rewrite_router_prompt | GROQ_LLM | JsonOutputParser()

email_category = 'customer_feedback'
draft_email = "Yo we can't help you, best regards Sarah"

print(rewrite_router.invoke({"initial_email": EMAIL, "email_category":email_category, "draft_email":draft_email}))



## Draft Email Analysis
draft_analysis_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are the Quality Control Agent read the INITIAL_EMAIL below  from a human that has emailed \
    our company email address, the email_category that the categorizer agent gave it and the \
    research from the research agent and write an analysis of how the email.

    Check if the DRAFT_EMAIL addresses the customer's issued based on the email category and the \
    content of the initial email.\n

    Give feedback of how the email can be improved and what specific things can be added or change\
    to make the email more effective at addressing the customer's issues.

    You never make up or add information that hasn't been provided by the research_info or in the initial_email.

    Return the analysis a JSON with a single key 'draft_analysis' and no premable or explaination.

    <|eot_id|><|start_header_id|>user<|end_header_id|>
    INITIAL_EMAIL: {initial_email} \n\n
    EMAIL_CATEGORY: {email_category} \n\n
    RESEARCH_INFO: {research_info} \n\n
    DRAFT_EMAIL: {draft_email} \n\n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email","email_category","research_info"],
)

draft_analysis_chain = draft_analysis_prompt | GROQ_LLM | JsonOutputParser()

email_category = 'customer_feedback'
research_info = None
draft_email = "Yo we can't help you, best regards Sarah"

email_analysis = draft_analysis_chain.invoke({"initial_email": EMAIL,
                                 "email_category":email_category,
                                 "research_info":research_info,
                                 "draft_email": draft_email})

print(email_analysis)



# Rewrite Email with Analysis
rewrite_email_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are the Final Email Agent read the email analysis below from the QC Agent \
    and use it to rewrite and improve the draft_email to create a final email.


    You never make up or add information that hasn't been provided by the research_info or in the initial_email.

    Return the final email as VALID JSON with a single key 'final_email' which is a string and no premable or explaination.


    <|eot_id|><|start_header_id|>user<|end_header_id|>
    EMAIL_CATEGORY: {email_category} \n\n
    RESEARCH_INFO: {research_info} \n\n
    DRAFT_EMAIL: {draft_email} \n\n
    DRAFT_EMAIL_FEEDBACK: {email_analysis} \n\n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email",
                     "email_category",
                     "research_info",
                     "email_analysis",
                     "draft_email",
                     ],
)

rewrite_chain = rewrite_email_prompt | GROQ_LLM | JsonOutputParser()

email_category = 'customer_feedback'
research_info = None
draft_email = "Yo we can't help you, best regards Sarah"

final_email = rewrite_chain.invoke({"initial_email": EMAIL,
                                 "email_category":email_category,
                                 "research_info":research_info,
                                 "draft_email": draft_email,
                                "email_analysis":email_analysis})

# final_email['final_email']