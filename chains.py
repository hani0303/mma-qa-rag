from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

MODEL_NAME = "gpt-4o"


class RouteQuery(BaseModel):

    # 데이터 소스 선택을 위한 리터럴 타입 필드
    binary_score: Literal["yes", "no"] = Field(
        ...,
        description="Given a user question, determine if it needs to be retrieved from vectorstore or not. Return 'yes' if it needs to be retrieved from vectorstore, otherwise return 'no'.",
    )
    # 벡터스토어에서 검색이 필요하면 "yes"를 반환하십시오.
    # 그렇지 않다면 "no"를 반환하십시오.


# chains.py에서 question router 프롬프트 수정
def create_question_router_chain():
    # LLM 초기화 및 함수 호출을 통한 구조화된 출력 생성
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
    structured_llm_router = llm.with_structured_output(RouteQuery)

   
    # Routing 을 위한 프롬프트 템플릿 생성
    system ="""You are an expert at routing user questions.
    The vectorstore contains documents related to RAG (Retrieval Augmented Generation).
    Always search the vectorstore first when processing any user query.
    Always return 'yes' regardless of the question content to ensure the vectorstore is queried.
    This approach guarantees that all questions, including follow-up questions in a conversation, 
    will be checked against the available documents before proceeding with other knowledge sources."""


    route_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "{question}"),
        ]
    )

    # 프롬프트 템플릿과 구조화된 LLM 라우터를 결합하여 질문 라우터 생성
    question_router = route_prompt | structured_llm_router

    return question_router


def create_question_rewrite_chain():
    # LLM 설정
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0)

    # Query Rewrite 시스템 프롬프트
    system = """You are a question re-writer that converts an input question to a better version that is optimized for vectorstore retrieval.
      Look at the input and try to reason about the underlying semantic intent / meaning. Always output results in Korean, 
      but if there are English terms in the input, include both Korean and English for those terms in your output. 
    If multiple languages are mixed in the input, maintain the same mix of languages in your output."""

    # 입력된 질문을 보고, 근본적인 의미와 의도를 분석하십시오.
    # 출력은 반드시 영어로 작성해야 합니다.

    # 프롬프트 정의
    re_write_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "Here is the initial question: \n\n {question} \n Formulate an improved question.",
            ),
        ]
    )

    # Question Re-writer 체인 초기화
    question_rewriter = re_write_prompt | llm | StrOutputParser()
    return question_rewriter


# 문서 평가를 위한 데이터 모델 정의
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
# """검색된 문서의 관련성을 확인하는 이진 점수."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )
# "문서가 질문과 관련이 있는 경우 'yes', 그렇지 않으면 'no'"


# chains.py에서 retrieval grader 프롬프트 수정
def create_retrieval_grader_chain():
    # LLM 초기화 및 함수 호출을 통한 구조화된 출력 생성
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
    structured_llm_grader = llm.with_structured_output(GradeDocuments)

    # 시스템 메시지와 사용자 질문을 포함한 프롬프트 템플릿 생성 - 관련성 기준 완화
    system = """You are a grader assessing relevance of a retrieved document to a user question.
        You should be generous in your assessment of relevance.
        If the document contains ANY keywords, concepts, or information that might help answer the user's question, grade it as relevant.
        Even if the document doesn't perfectly match the question, but has some related information, consider it relevant.
        This is NOT a stringent test - the goal is to include potentially useful documents while filtering out completely irrelevant ones.
        When in doubt, consider the document relevant (return 'yes').
        Give a binary score 'yes' or 'no' to indicate whether the document is relevant to the question."""

    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "Retrieved document: \n\n {document} \n\n User question: {question}",
            ),
        ]
    )

    # 문서 검색결과 평가기 생성
    retrieval_grader = grade_prompt | structured_llm_grader
    return retrieval_grader


# 할루시네이션 체크를 위한 데이터 모델 정의
class AnswerGroundedness(BaseModel):
    """Binary score for answer groundedness."""
# binary_score라는 변수는 답변의 근거성(groundedness)을 이진법적으로 평가하기 위한 것입니다.
    binary_score: str = Field(
        description="Answer is grounded in the facts(given context), 'yes' or 'no'"
    )

# 이는 "답변이 (주어진 맥락의) 사실에 근거하고 있는지, '예' 또는 '아니오'로 표시"라는 의미입니다.
def create_groundedness_checker_chain():
    # LLM 설정
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
    structured_llm_grader = llm.with_structured_output(AnswerGroundedness)

    # 프롬프트 설정
    system = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
        Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""
    
    
    # 당신은 LLM(대규모 언어 모델)의 생성물이 검색된 사실 집합에 기반하여 지지되는지를 평가하는 평가자입니다. 
    # \n '예' 또는 '아니오'로 이진 점수를 부여하세요. '예'는 답변이 사실 집합에 기반하여 지지된다는 것을 의미합니다.

    # 이 질문은 주어진 답변이 특정 사실에 기반하여 신뢰할 수 있는지를 평가하라는 요청입니다. 
    # '예'는 답변이 사실에 기반하고 있음을 나타내고, '아니오'는 그렇지 않음을 나타냅니다.
    # 프롬프트 템플릿 생성
    groundedness_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "Set of facts: \n\n {documents} \n\n LLM generation: {generation}",
            ),
        ]
    )

    # 답변의 환각 여부 평가기 생성
    groundedness_checker = groundedness_prompt | structured_llm_grader
    return groundedness_checker


class GradeAnswer(BaseModel):
    """Binary scoring to evaluate the appropriateness of answers to questions"""
#이는 주어진 답변이 질문에 적절한지를 평가하기 위해 '예' 또는 '아니오'로 점수를 매기는 것을 의미합니다.
    binary_score: str = Field(
        description="Indicate 'yes' or 'no' whether the answer solves the question"
    )


def create_answer_grade_chain():
    # 함수 호출을 통한 LLM 초기화
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
    structured_llm_grader = llm.with_structured_output(GradeAnswer)

    # 프롬프트 설정
    system = """You are a grader assessing whether an answer addresses / resolves a question \n 
        Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""
    #"당신은 답변이 질문을 다루고/해결하는지를 평가하는 채점자입니다. \n '예' 또는 '아니오'로 이진 점수를 부여하세요.
    #  '예'는 답변이 질문을 해결함을 의미합니다."
    relevant_answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "User question: \n\n {question} \n\n LLM generation: {generation}",
            ),
        ]
    )

    # 프롬프트 템플릿과 구조화된 LLM 평가기를 결합하여 답변 평가기 생성
    relevant_answer_checker = relevant_answer_prompt | structured_llm_grader
    return relevant_answer_checker
