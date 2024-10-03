from chains.rag_chain import rag_chain
from utils import write_markdown_file


# # RAG node
# def research_info_search(state):
#     print("---RESEARCH INFO RAG---")
#     initial_prompt = state["initial_prompt"]
#     medical_report = state["medical_report"]
#     num_steps = state['num_steps']
#     num_steps += 1
#     # Web search
#     questions = rag_chain.invoke({"initial_prompt": initial_prompt,
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


# Updated research_info_search node
def research_info_search(state):
    print("---RESEARCH INFO RAG---")
    medical_report = state["medical_report"]
    num_steps = state['num_steps']
    num_steps += 1

    # Perform RAG search using the medical report
    rag_results = rag_chain.invoke({"medical_report": medical_report})
    state["research_info"] = rag_results
    print("===RAG RESULTS===")
    print(rag_results)
    write_markdown_file([rag_results], "clinical_trials")

    return {
        "research_info": [rag_results],
        "num_steps": num_steps
    }
