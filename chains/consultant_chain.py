from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

conversation_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a top medical doctor, and you will ask questions to a patient about
    their condition. Your questions are designed to get all the necessary information
    to determine which clinical trials are the best fit for the patient. 
    Always consider the full conversation history when asking new questions."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", """Ask the patient a relevant question about their condition to gather more information.
    Do not generate a medical report yet, just ask a single question.
    Make sure your question is based on the conversation so far and doesn't repeat information already gathered.

    PATIENT PROMPT:

    {initial_prompt}
    """)
])

report_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a top medical doctor. Based on the conversation with the patient,
    you will write a medical report used by other doctors to find the best clinical trials for the patient."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", """Based on the conversation, provide a medical report about the patient's condition.
    This report will be read by other doctors and used to find the best clinical trials for the patient.""")
])

conversation_chain = conversation_prompt | GROQ_LLM | StrOutputParser()
report_chain = report_prompt | GROQ_LLM | StrOutputParser()

# Export both chains
consultant_chain = {
    "conversation": conversation_chain,
    "report": report_chain
}