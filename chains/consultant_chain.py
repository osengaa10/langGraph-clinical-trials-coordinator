from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM, CHAT_LLM  # You might need to change this import depending on the LLM you're using
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


conversation_prompt = PromptTemplate(
    template="""<s>[INST] <<SYS>>
You are a top medical doctor, and you will ask questions to a patient about
their condition. Your questions are designed to get all the necessary information
to determine which clinical trials are the best fit for the patient. 
Always consider the full conversation history when asking new questions.

After each question and answer, evaluate if you have enough information to generate a comprehensive medical report.
If you do, indicate that you're ready to generate the report. If not, ask another relevant question.
<</SYS>>

Based on the conversation so far, either ask a relevant question to gather more information
or indicate that you have enough information to generate a medical report.

Your response should be in JSON format with the following structure:
{{
    "action": "ask_question" or "generate_report",
    "content": "Your question or a message indicating you're ready to generate the report"
}}

Again, ONLY output valid JSON and nothing else.

PATIENT PROMPT:

{initial_prompt}

CONVERSATION HISTORY:

{chat_history}
[/INST]
""",
    input_variables=["initial_prompt", "chat_history"],
)


# conversation_prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are a top medical doctor, and you will ask questions to a patient about
#     their condition. Your questions are designed to get all the necessary information
#     to determine which clinical trials are the best fit for the patient. 
#     Always consider the full conversation history when asking new questions.
    
#     After each question and answer, evaluate if you have enough information to generate a comprehensive medical report.
#     If you do, indicate that you're ready to generate the report. If not, ask another relevant question."""),
#     MessagesPlaceholder(variable_name="chat_history", optional=True),
#     ("human", """Based on the conversation so far, either ask a relevant question to gather more information
#     or indicate that you have enough information to generate a medical report.

#     Your response should be in JSON format with the following structure:
#     {{
#         "action": "ask_question" or "generate_report",
#         "content": "Your question or a message indicating you're ready to generate the report"
#     }}
    
#     Again, ONLY output valid JSON and nothing else.

#     PATIENT PROMPT:

#     {initial_prompt}
#     """)
# ])


report_prompt = PromptTemplate(
    template="""<s>[INST] <<SYS>>
You are a top medical doctor. Based on the conversation with the patient,
you will write a medical report used by other doctors to find the best clinical trials for the patient.
<</SYS>>

Based on the conversation, provide a comprehensive medical report about the patient's condition.
This report will be read by other doctors and used to find the best clinical trials for the patient.
Include all relevant details such as symptoms, medical history, current medications, and any other factors
that might be important for clinical trial eligibility.

CONVERSATION HISTORY:

{chat_history}
[/INST]
""",
    input_variables=["chat_history"],
)

# conversation_chain = conversation_prompt | CHAT_LLM | JsonOutputParser()

conversation_chain = conversation_prompt | GROQ_LLM | JsonOutputParser()


report_chain = report_prompt | GROQ_LLM | StrOutputParser()

# Export both chains
consultant_chain = {
    "conversation": conversation_chain,
    "report": report_chain
}