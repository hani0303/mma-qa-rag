from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from operator import itemgetter
from langchain_core.prompts import load_prompt
import urllib.parse

# rag.py 파일의 create_rag_chain 함수를 다음과 같이 수정하세요

def create_rag_chain(prompt_name="code-rag-prompt", model_name="gpt-4o"):
    """
    RAG 체인을 생성합니다.
    """
    # RAG 문서를 포맷팅하는 함수
    def format_rag_docs(docs):
        """문서를 XML 형식으로 포맷팅"""
        formatted = "\n\n".join(
            [
                f'<document><content>{doc.page_content}</content><source>{urllib.parse.unquote(doc.metadata.get("source", "unknown"))}</source><page>{doc.metadata.get("page", 0) + 1 if "page" in doc.metadata else "N/A"}</page></document>'
                for doc in docs
            ]
        )
        return formatted
    
    # 대화 이력을 포맷팅하는 함수
    def format_chat_history(chat_history):
        """대화 이력을 텍스트로 포맷팅"""
        if not chat_history or len(chat_history) == 0:
            return ""
            
        formatted = "\n".join(
            [
                f"User: {msg.content}" if msg.type == "human" else f"Assistant: {msg.content}"
                for msg in chat_history
            ]
        )
        return formatted

    # 프롬프트 로드 - UTF-8 인코딩 명시
    rag_prompt = load_prompt(f"prompts/{prompt_name}.yaml", encoding="utf-8")

    # LLM 설정
    llm = ChatOpenAI(model_name=model_name, temperature=0)

    # 체인 생성
    rag_chain = (
        {
            "question": itemgetter("question"),
            "context": lambda x: format_rag_docs(x["context"]) if isinstance(x["context"], list) else x["context"],
            "chat_history": lambda x: format_chat_history(x.get("chat_history", [])),
        }
        | rag_prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain