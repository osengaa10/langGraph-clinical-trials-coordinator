from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM
from langchain.prompts import PromptTemplate


trials_search_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    As a top medical expert and software engineer, you will use the key words
    from the Prompt Distiller to fetch a list of all relevant clinical trials. \n

    <|eot_id|><|start_header_id|>user<|end_header_id|>
    SEARCH_TERM: {search_term} \n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["search_term"],
)

trials_search_chain = trials_search_prompt | GROQ_LLM | StrOutputParser()

search_term = 'sarcoma'
print(":::trials_search_chain invoked:::")
print(trials_search_chain.invoke({"search_term":search_term}))
print(":::trials_search_chain invoked:::")
