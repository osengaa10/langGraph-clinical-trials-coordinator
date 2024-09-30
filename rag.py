from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import time
import LLMs.llm as llm


persist_directory = f'db'

################################################################################
# split documents into chunks, create embeddings, store embeddings in chromaDB #
################################################################################
def chunk_and_embed():
    src_dir = f'./studies'
    dst_dir = f'./rag_data/data'
    files = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
    persist_directory = f'db'
    t1 = time.perf_counter()
    try:
        """split documents into chunks, create embeddings, store embeddings in chromaDB"""
        # Load each text file as a separate document
        documents = []
        for file in files:
            file_path = os.path.join(src_dir, file)
            with open(file_path, 'r') as f:
                text = f.read()
                document = Document(page_content=text, metadata={'source': file_path})
                documents.append(document)
        
        print(f' =========== number of documents {len(documents)} =========== ')
     
        Chroma.from_documents(documents=documents,
                              embedding=llm.embedding,
                              persist_directory=persist_directory)

        t2 = time.perf_counter()
        print(f'time taken to embed {len(documents)} chunks:',t2-t1)
        print(f'time taken to embed {len(documents)} chunks:,{(t2-t1)/60} minutes')
        print(f'time taken to embed {len(documents)} chunks:,{((t2-t1)/60)/60} hours')

        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        print(f"Moved {len(files)} files from {src_dir} to {dst_dir}.")
        print(f"Files moved: {files}")
        print("\n".join(files))
        
        return f'time taken to embed {len(documents)} chunks:,{(t2-t1)/60} minutes'

    except Exception as e:
        for file in files:
            src_file_path = os.path.join(src_dir, file)
            os.remove(src_file_path)
        print(f"ERROR NOOOOOOOOO: {e}")



# # chunk_and_embed(embedding)
# vectordb = Chroma.from_documents(documents=texts,
#                                  embedding=embedding,
#                                  persist_directory=persist_directory)


vectordb = Chroma(embedding_function=llm.embedding, persist_directory=persist_directory)


