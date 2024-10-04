from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser

conversation_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a top medical doctor, and you will ask questions to a patient about
    their condition. Your questions are designed to get all the necessary information
    to determine which clinical trials are the best fit for the patient. 
    Always consider the full conversation history when asking new questions.
    
    After each question and answer, evaluate if you have enough information to generate a comprehensive medical report.
    If you do, indicate that you're ready to generate the report. If not, ask another relevant question."""),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", """Based on the conversation so far, either ask a relevant question to gather more information
    or indicate that you have enough information to generate a medical report.
    
    Your response should be in JSON format with the following structure:
    {{
        "action": "ask_question" or "generate_report",
        "content": "Your question or a message indicating you're ready to generate the report"
    }}

    PATIENT PROMPT:

    {initial_prompt}
    """)
])

report_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a top medical doctor. Based on the conversation with the patient,
    you will write a medical report used by other doctors to find the best clinical trials for the patient."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", """Based on the conversation, provide a comprehensive medical report about the patient's condition.
    This report will be read by other doctors and used to find the best clinical trials for the patient.
    Include all relevant details such as symptoms, medical history, current medications, and any other factors
    that might be important for clinical trial eligibility.""")
])

conversation_chain = conversation_prompt | GROQ_LLM | JsonOutputParser()
report_chain = report_prompt | GROQ_LLM | StrOutputParser()

# Export both chains
consultant_chain = {
    "conversation": conversation_chain,
    "report": report_chain
}