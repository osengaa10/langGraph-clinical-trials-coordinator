from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.merge import MergedDataLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
import os
import time
import LLMs.llm as llm
# loader_csv = CSVLoader(file_path="./studies/westworld_resort_facts.csv")
# loader_all = MergedDataLoader(loaders=[loader_csv]) #loader_web, loader_txt,]
# docs_all = loader_all.load()
# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
# texts = text_splitter.split_documents(docs_all)

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
        print("4......inside chunk_and_embed try statement")
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
        # chunk_size = 2000
        # chunk_overlap=20
        # print(f"split TXT files")
        # print(os.listdir(src_dir))
        # loader = DirectoryLoader(src_dir, glob="./*.txt", loader_cls=TextLoader)

        # documents = loader.load()
        # print(f' =========== number of documents {len(documents)} =========== ')
        # #splitting the text into
        # text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        # texts = text_splitter.split_documents(documents)
        # print(f'=========== number of chunks {len(texts)} ===========')
     
        # Chroma.from_documents(documents=texts,
        #                                 embedding=llm.embedding,
        #                                 persist_directory=persist_directory)

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


