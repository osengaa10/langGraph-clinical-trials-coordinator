from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a top medical doctor, and you will ask questions to a patient about
    their condition. Your questions are designed to get all the necessary information
    to determine which clinical trials are the best fit for the patient."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", """Ask the patient questions about their condition to gather enough information
    to write a paragraph long medical report. Your medical report will be read
    by other doctors.

    Output a one paragraph medical report about patient's condition.

    PATIENT PROMPT:

    {initial_prompt}
    """)
])

consultant_chain = prompt | GROQ_LLM | StrOutputParser()