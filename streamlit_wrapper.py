from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
import os
import time
import pickle
import hashlib
from retrievers import init_retriever
from states import GraphState
from rag import create_rag_chain
from nodes import *
from document_manager import VECTOR_DB_FOLDER, load_db_metadata

# 글로벌 DB 캐시 저장소
db_cache = {}
# 그래프 로드 완료 플래그
GRAPHS_LOADED = False

def preload_vector_dbs():
    """모든 벡터 DB를 미리 메모리에 로드하는 함수"""
    global db_cache
    
    # 실제 존재하는 벡터 DB 디렉토리 확인
    existing_folders = [folder for folder in os.listdir() if folder.startswith(VECTOR_DB_FOLDER) and os.path.isdir(folder)]
    metadata = load_db_metadata()
    
    print(f"벡터 DB 사전 로드 시작: {len(existing_folders)}개 DB 대상")
    
    for folder in existing_folders:
        try:
            # 각 벡터 DB에 대한 retriever 생성 및 캐싱
            print(f"벡터 DB '{folder}' 로드 중...")
            start_time = time.time()
            retriever = init_retriever(db_index=folder)
            load_time = time.time() - start_time
            
            # 표시 이름 가져오기
            display_name = metadata.get(folder, {}).get('display_name', folder[len(VECTOR_DB_FOLDER):])
            
            # 캐시에 저장
            db_cache[folder] = {
                'retriever': retriever,
                'display_name': display_name,
                'graph': None,  # 그래프는 별도 함수에서 생성
                'load_time': load_time
            }
            print(f"벡터 DB '{display_name}' 로드 완료 - 소요 시간: {load_time:.2f}초")
        except Exception as e:
            print(f"벡터 DB '{folder}' 로드 중 오류: {str(e)}")
    
    print(f"벡터 DB 사전 로드 완료: {len(db_cache)}개 DB 로드됨")
    return db_cache

def create_graph_internal(db_index, retriever):
    """내부적으로 그래프를 생성하는 함수"""
    # RAG 체인 생성
    rag_chain = create_rag_chain()
    
    # 그래프 상태 초기화
    workflow = StateGraph(GraphState)
    
    # 노드 정의 - 간결하게 필수 노드만 추가
    workflow.add_node("retrieve", RetrieveNode(retriever))
    workflow.add_node("web_search", WebSearchNode())
    workflow.add_node("generate_answer", RagAnswerNode(rag_chain))
    
    # 엣지 추가 - 단순화된 흐름
    # 시작 -> 검색 -> 결과에 따라 분기 -> 답변 생성 -> 종료
    workflow.add_edge(START, "retrieve")
    
    workflow.add_conditional_edges(
        "retrieve",
        check_documents,
        {
            "has_documents": "generate_answer",  # 검색 결과가 있으면 답변 생성
            "no_documents": "web_search",        # 검색 결과가 없으면 웹 검색
        },
    )
    
    workflow.add_edge("web_search", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    # 그래프 컴파일
    app = workflow.compile(checkpointer=MemorySaver())
    
    return app

def preload_graphs():
    """모든 DB에 대한 그래프를 미리 생성하는 함수"""
    global db_cache, GRAPHS_LOADED
    
    # 이미 그래프가 로드되었으면 건너뜀
    if GRAPHS_LOADED:
        print("그래프가 이미 로드되어 있습니다. 그래프 생성 과정을 건너뜁니다.")
        return
    
    print(f"그래프 사전 생성 시작: {len(db_cache)}개 DB 대상")
    total_start = time.time()
    
    for db_id in list(db_cache.keys()):
        try:
            # 이미 그래프가 생성되어 있으면 스킵
            if db_cache[db_id].get('graph') is not None:
                print(f"DB '{db_id}'의 그래프 이미 생성됨 - 스킵")
                continue
                
            print(f"DB '{db_id}'의 그래프 생성 중...")
            start_time = time.time()
            
            # 그래프 생성
            graph = create_graph_internal(db_id, db_cache[db_id]['retriever'])
            
            # 생성된 그래프를 캐시에 저장
            db_cache[db_id]['graph'] = graph
            
            graph_time = time.time() - start_time
            db_cache[db_id]['graph_time'] = graph_time
            
            print(f"DB '{db_id}'의 그래프 생성 완료 - 소요 시간: {graph_time:.2f}초")
        except Exception as e:
            print(f"DB '{db_id}'의 그래프 생성 중 오류: {str(e)}")
    
    total_time = time.time() - total_start
    print(f"모든 그래프 사전 생성 완료 - 총 소요 시간: {total_time:.2f}초")
    
    # 모든 그래프 로드 완료 플래그 설정
    GRAPHS_LOADED = True

def create_graph(db_index=None):
    """그래프 생성 함수 - 캐시된 그래프 활용"""
    global db_cache, GRAPHS_LOADED
    
    # db_index가 None인 경우 처리
    if not db_index:
        return None
    
    # 서버가 이미 로드되었고, 캐시에 DB가 있는 경우
    if GRAPHS_LOADED and db_index in db_cache:
        # 이미 그래프가 생성되어 있으면 즉시 반환
        if db_cache[db_index].get('graph') is not None:
            print(f"캐시된 그래프 즉시 반환 - DB: {db_index}")
            return db_cache[db_index]['graph']
    
    # 서버 최초 시작 시나 캐시에 없는 경우
    try:
        # 캐시에 해당 DB가 있는지 확인
        if db_index in db_cache:
            # 그래프 생성 및 캐시
            print(f"캐시된 retriever로 그래프 생성 - DB: {db_index}")
            retriever = db_cache[db_index]['retriever']
            graph = create_graph_internal(db_index, retriever)
            db_cache[db_index]['graph'] = graph
            return graph
        else:
            # 캐시에 없는 경우 새로 로드 (예외 상황)
            print(f"DB '{db_index}'가 캐시에 없음 - 새로 로드")
            retriever = init_retriever(db_index=db_index)
            
            # 새로 로드한 DB도 캐시에 추가
            db_cache[db_index] = {
                'retriever': retriever,
                'display_name': db_index[len(VECTOR_DB_FOLDER):],
                'graph': None,
                'load_time': 0
            }
            
            # 그래프 생성
            graph = create_graph_internal(db_index, retriever)
            db_cache[db_index]['graph'] = graph
            return graph
    except Exception as e:
        print(f"그래프 생성 중 오류: {str(e)}")
        return None

def stream_graph(app, query, streamlit_container, thread_id):
    """그래프 실행 및 스트리밍 함수"""
    # 그래프 실행
    result = app.invoke({
        "question": query,
        "documents": []
    })
    
    # 결과 출력
    if "generation" in result:
        streamlit_container.markdown(result["generation"])
        return result["generation"]
    else:
        streamlit_container.markdown("답변을 생성하지 못했습니다.")
        return "답변을 생성하지 못했습니다."

def init_app():
    """Flask 앱 시작 시 호출되는 초기화 함수"""
    global GRAPHS_LOADED
    
    if GRAPHS_LOADED:
        print("앱이 이미 초기화되어 있습니다.")
        return
    
    print("앱 초기화 시작...")
    
    # 벡터 DB 로드 및 그래프 생성
    preload_vector_dbs()
    preload_graphs()
    
    GRAPHS_LOADED = True
    print("앱 초기화 완료")
    return db_cache

# 시스템 상태 관리 함수들
def save_system_state():
    """시스템 상태와 그래프를 저장"""
    try:
        save_data = {
            'db_indices': list(db_cache.keys()),
            'db_display_names': {k: v.get('display_name', k) for k, v in db_cache.items()},
            'loaded': GRAPHS_LOADED,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open('system_state.pkl', 'wb') as f:
            pickle.dump(save_data, f)
        
        # 그래프 상태 별도 저장 (그래프는 복잡한 객체이므로 별도 저장)
        graphs = {db_id: data['graph'] for db_id, data in db_cache.items() if 'graph' in data}
        with open('saved_graphs.pkl', 'wb') as f:
            pickle.dump(graphs, f)
            
        print("시스템 상태 및 그래프 저장 완료")
        return True
    except Exception as e:
        print(f"상태 저장 중 오류: {str(e)}")
        return False

def restore_system_state():
    """저장된 시스템 상태와 그래프를 복원"""
    global db_cache, GRAPHS_LOADED
    
    try:
        if os.path.exists('system_state.pkl'):
            with open('system_state.pkl', 'rb') as f:
                saved_data = pickle.load(f)
            
            # 기본 상태 복원
            preload_vector_dbs()
            
            # 그래프 상태 복원
            preload_graphs()
            
            print("시스템 상태 복원 완료")
            return True
    except Exception as e:
        print(f"상태 복원 중 오류: {str(e)}")
        return False