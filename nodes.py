from langchain_core.documents import Document
from langchain_teddynote.tools.tavily import TavilySearch
from states import GraphState
from abc import ABC, abstractmethod

class BaseNode(ABC):
    """기본 노드 클래스"""
    def __init__(self, **kwargs):
        self.name = "BaseNode"
        self.verbose = kwargs.get("verbose", False)

    @abstractmethod
    def execute(self, state: GraphState) -> GraphState:
        pass

    def __call__(self, state: GraphState):
        return self.execute(state)

class RetrieveNode(BaseNode):
    """문서 검색 노드"""
    def __init__(self, retriever, **kwargs):
        super().__init__(**kwargs)
        self.name = "RetrieveNode"
        self.retriever = retriever
        # 캐시 추가
        self.cache = {}

    def execute(self, state: GraphState) -> GraphState:
        question = state["question"]
        
        # 이미 캐시에 있는지 확인
        if question in self.cache:
            documents = self.cache[question]
            print(f"[{self.name}] 캐시에서 문서 {len(documents)}개 로드됨")
        else:
            documents = self.retriever.invoke(question)
            # 결과를 캐시에 저장
            self.cache[question] = documents
            print(f"[{self.name}] 문서 {len(documents)}개 검색됨")
            
        return GraphState(question=question, documents=documents)

class RagAnswerNode(BaseNode):
    """RAG 답변 생성 노드"""
    def __init__(self, rag_chain, **kwargs):
        super().__init__(**kwargs)
        self.name = "RagAnswerNode"
        self.rag_chain = rag_chain

    def execute(self, state: GraphState) -> GraphState:
        question = state["question"]
        documents = state["documents"]
        chat_history = state.get("chat_history", [])  # 대화 히스토리 가져오기
        
        # chat_history가 None인 경우 빈 리스트로 초기화
        if chat_history is None:
            chat_history = []
        
        # 답변 생성 시 대화 히스토리 전달
        answer = self.rag_chain.invoke({
            "context": documents, 
            "question": question,
            "chat_history": chat_history
        })
        
        return GraphState(
            question=question, 
            documents=documents, 
            generation=answer,
            chat_history=chat_history
        )

class WebSearchNode(BaseNode):
    """웹 검색 노드"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "WebSearchNode"
        self.web_search_tool = TavilySearch(max_results=3)

    def execute(self, state: GraphState) -> GraphState:
        question = state["question"]
        web_results = self.web_search_tool.invoke({"query": question})
        web_results_docs = [
            Document(
                page_content=web_result["content"],
                metadata={"source": web_result["url"]},
            )
            for web_result in web_results
        ]
        return GraphState(question=question, documents=web_results_docs)

def check_documents(state: GraphState) -> str:
    """문서 존재 여부 확인 함수"""
    documents = state.get("documents", [])
    return "has_documents" if documents else "no_documents"