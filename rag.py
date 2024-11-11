from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import time
import LLMs.llm as llm

def create_vector_db(uid):
    persist_directory = f'db/{uid}'
    vectordb = Chroma(embedding_function=llm.embedding, persist_directory=persist_directory)
    return vectordb



def chunk_and_embed(new_studies, uid):
    vectordb = create_vector_db(uid)
    t1 = time.perf_counter()
    try:
        documents = []
        for file_name, file_path in new_studies:
            with open(file_path, 'r') as f:
                text = f.read()
                document = Document(page_content=text, metadata={'source': file_path})
                documents.append(document)
        
        print(f' =========== number of new documents {len(documents)} =========== ')
        
        # vectordb.add_documents(documents)
        Chroma.from_documents(documents=documents,
                            embedding=llm.embedding,
                            persist_directory=f'db/{uid}')

        t2 = time.perf_counter()
        print(f'time taken to embed {len(documents)} new chunks: {(t2-t1)/60} minutes')

        # Move processed files to a different directory
        dst_dir = f'./rag_data/data/{uid}'
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        
        for file_name, src_file_path in new_studies:
            dst_file_path = os.path.join(dst_dir, file_name)
            os.rename(src_file_path, dst_file_path)

        print(f"Moved {len(new_studies)} files to {dst_dir}.")
        
        return vectordb

    except Exception as e:
        print(f"ERROR: {e}")
        # Clean up in case of error
        for _, file_path in new_studies:
            if os.path.exists(file_path):
                os.remove(file_path)