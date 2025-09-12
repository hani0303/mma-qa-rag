import streamlit as st
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import JinaRerank
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain.retrievers import  EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

def init_retriever(db_index="db_index", fetch_k=10, top_n=3):
       
    # bm25 retriever와 faiss retriever를 초기화합니다.
    bm25_retriever = BM25Retriever.from_texts(
        db_index,
    )
    bm25_retriever.k = 3  # BM25Retriever의 검색 결과 개수를 3로 설정합니다.

    # Embeddings 설정
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    # 저장된 DB 로드
    langgraph_db = FAISS.load_local(
        db_index, embeddings, allow_dangerous_deserialization=True
    )
    # retriever 생성
    code_retriever = langgraph_db.as_retriever(search_kwargs={"k": fetch_k})

    # 앙상블 retriever를 초기화합니다.
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, code_retriever],
        weights=[0.7, 0.3],
    )
    
    # JinaRerank 및 ContextualCompressionRetriever 부분 제거하고
    # ensemble_retriever를 직접 반환합니다
    return ensemble_retriever