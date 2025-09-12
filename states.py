# states.py 파일을 다음과 같이 수정하세요

from typing import List, Dict, Any
from typing_extensions import TypedDict, Annotated


# 그래프의 상태 정의
class GraphState(TypedDict):
    """
    그래프의 상태를 나타내는 데이터 모델

    Attributes:
        question: 사용자 질문
        documents: 검색된 문서 리스트
        generation: 생성된 답변
        chat_history: 이전 대화 내용
    """
    question: Annotated[str, "User question"]
    documents: Annotated[List, "Retrieved documents"]
    generation: Annotated[str, "Generated answer"]
    chat_history: Annotated[List, "Chat history"]
