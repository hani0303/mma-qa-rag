from flask import Flask, render_template, request, jsonify, session, Response
from flask_session import Session
import uuid
import os
import json
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_teddynote import logging
from langchain_teddynote.messages import random_uuid
from langsmith import Client

# 기존 모듈 import
from streamlit_wrapper import create_graph, init_app, db_cache, stream_graph
from document_manager import setup_document_manager, load_db_metadata, get_db_display_name, VECTOR_DB_FOLDER

# 파일 상단에 필요한 임포트 추가
import queue
import threading

load_dotenv()

# 앱 초기화 전에 전역 변수 설정
INITIALIZED = False  # 앱 초기화 여부를 추적하는 플래그

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션 암호화를 위한 키
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# 프로젝트 이름 설정
LANGSMITH_PROJECT = " Document-QA-RAG"

# LangSmith 추적 설정
logging.langsmith(LANGSMITH_PROJECT)

# 전역 변수: 현재 사용 중인 그래프 저장
current_graph = None
current_db_index = None

# 앱 초기화 - 한 번만 실행되도록 수정
def initialize_app():
    global INITIALIZED, db_cache
    if not INITIALIZED:
        print("앱 초기화 - 벡터 DB 및 그래프 사전 로드 시작")
        init_app()
        print("앱 초기화 - 벡터 DB 및 그래프 사전 로드 완료")
        print(f"로드된 DB 캐시 키 목록: {list(db_cache.keys())}")

        # 사전 로드된 DB 수 확인 및 로그
        db_with_graphs = sum(1 for db in db_cache.values() if db.get('graph') is not None)
        print(f"그래프가 생성된 DB 수: {db_with_graphs}/{len(db_cache)}")
        
        INITIALIZED = True  # 초기화 완료 표시
    else:
        print("앱이 이미 초기화되어 있습니다. 초기화 과정을 건너뜁니다.")

# 앱 시작 시 초기화 실행
initialize_app()

# 문서 관리자 설정
app = setup_document_manager(app)

@app.route('/')
def index():
    # 세션 초기화
    if 'messages' not in session:
        session['messages'] = []
    if 'thread_id' not in session:
        session['thread_id'] = str(uuid.uuid4())
    
    # 모든 벡터 DB 가져오기 (카테고리 정보 포함)
    vector_dbs = []
    metadata = load_db_metadata()
    
    # db_cache에서 정보 가져오기 (미리 로드된 DB)
    for db_id, db_info in db_cache.items():
        # 메타데이터에서 카테고리 정보 가져오기
        db_metadata = metadata.get(db_id, {})
        
        # 표시 이름 가져오기 - 캐시에서 우선 사용, 없으면 메타데이터 사용
        display_name = db_info.get('display_name') or db_metadata.get('display_name')
        if not display_name:
            display_name = db_id[len(VECTOR_DB_FOLDER):]
        
        # 카테고리 정보 가져오기 - 없으면 기타로 설정
        category = db_metadata.get('category', '기타')
        
        # 그래프 사전 로드 여부 확인 (디버깅용)
        has_graph = 'graph' in db_info and db_info['graph'] is not None
        
        vector_dbs.append({
            'id': db_id,
            'name': display_name,
            'category': category,
            'has_graph': has_graph  # 클라이언트에서는 사용하지 않지만 디버깅용
        })
    
    return render_template('index.html', messages=session.get('messages', []), vector_dbs=vector_dbs)

@app.route('/ask', methods=['POST'])
def ask():
    global current_graph, current_db_index
    
    data = request.json
    user_input = data.get('question', '')
    thread_id = data.get('thread_id', str(uuid.uuid4()))
    
    # 벡터 DB 선택 여부 확인
    if 'db_index' not in session or not session.get('db_index'):
        return jsonify({
            'error': '벡터 DB를 선택해주세요. 좌측 사이드바에서 DB를 선택한 후 질문해주세요.',
            'status': 'no_db_selected'
        }), 400
    
    # 메시지 저장
    add_message('user', user_input)
    
    try:
        # 현재 세션의 DB_index로 그래프 가져오기 (이미 로드되어 있음)
        db_index = session.get('db_index')
        
        # 현재 그래프가 없거나 DB가 변경된 경우에만 새로 가져옴
        if current_graph is None or current_db_index != db_index:
            print(f"현재 그래프가 없거나 DB가 변경됨 - 그래프 로드: {db_index}")
            current_graph = create_graph(db_index)
            current_db_index = db_index
        else:
            print(f"기존 그래프 재사용 - DB: {current_db_index}")
        
        # 그래프 실행
        print(f"그래프 실행 시작")
        start_time = time.time()
        result = run_graph(current_graph, user_input, thread_id)
        elapsed_time = time.time() - start_time
        print(f"그래프 실행 완료 - 소요 시간: {elapsed_time:.2f}초")
        
        ai_answer = result.get('generation', '답변을 생성하지 못했습니다.')
        
        # AI 답변 저장
        add_message('assistant', ai_answer)
        
        return jsonify({
            'answer': ai_answer,
            'status': 'success'
        })
    except Exception as e:
        print(f"ask 라우트 오류: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    feedback = {
        '올바른 답변': data.get('correctness', 5),
        '도움됨': data.get('helpfulness', 5),
        '구체성': data.get('specificity', 5),
        '의견': data.get('comment', '')
    }
    
    try:
        client = Client()
        run = next(iter(client.list_runs(project_name=LANGSMITH_PROJECT, limit=1)))
        parent_run_id = run.parent_run_ids[0]
        
        for key, value in feedback.items():
            if key in ["올바른 답변", "도움됨", "구체성"]:
                client.create_feedback(parent_run_id, key, score=value)
            elif key == "의견" and value:
                client.create_feedback(parent_run_id, key, comment=value)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 전역 변수: 처리 단계를 저장할 큐 생성
progress_queues = {}

@app.route('/stream_progress', methods=['GET'])
def stream_progress():
    """처리 단계를 실시간으로 스트리밍하는 엔드포인트"""
    thread_id = request.args.get('thread_id')
    
    if not thread_id or thread_id not in progress_queues:
        # 쓰레드 ID가 없거나 해당 큐가 없으면 새로운 큐 생성
        thread_id = str(time.time())
        progress_queues[thread_id] = queue.Queue()
    
    def generate():
        q = progress_queues[thread_id]
        
        # 초기 메시지 전송
        yield f"data: {json.dumps({'step': '🧑‍💻 질문의 의도를 분석하는 중입니다.'})}\n\n"
        
        # 큐에서 메시지 계속 가져오기
        timeout_counter = 0
        while timeout_counter < 60:  # 최대 60초 대기
            try:
                message = q.get(block=True, timeout=1.0)
                if message == "DONE":
                    # 종료 신호를 받으면 루프 종료
                    break
                yield f"data: {json.dumps({'step': message})}\n\n"
                timeout_counter = 0
            except queue.Empty:
                timeout_counter += 1
        
        # 종료 메시지 전송
        yield "data: {\"done\": true}\n\n"
        
        # 사용이 끝난 큐 정리
        if thread_id in progress_queues:
            del progress_queues[thread_id]
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/change_db', methods=['POST'])
def change_db():
    global current_graph, current_db_index
    
    data = request.json
    db_index = data.get('db_index')
    
    if not db_index:
        return jsonify({
            'status': 'error', 
            'message': 'DB 인덱스가 제공되지 않았습니다.'
        }), 400
    
    try:
        print(f"DB 변경 시작 - 인덱스: {db_index}")
        start_time = time.time()
        
        # 캐시에서 바로 그래프 가져오기
        if db_index in db_cache and db_cache[db_index].get('graph') is not None:
            print(f"사전 생성된 그래프 즉시 사용 - DB: {db_index}")
            current_graph = db_cache[db_index]['graph']
        else:
            print(f"캐시에 그래프 없음 - 새로 생성: {db_index}")
            current_graph = create_graph(db_index)
        
        # 현재 DB 인덱스 업데이트
        current_db_index = db_index
        
        # 세션에 DB 선택 저장
        session['db_index'] = db_index
        
        # 세션 초기화 (새 DB에 대한 새 대화 시작)
        session['messages'] = []
        session['thread_id'] = str(uuid.uuid4())
        
        # DB 표시 이름 가져오기 - 캐시에서 직접 가져옴
        display_name = db_cache.get(db_index, {}).get('display_name')
        if not display_name:
            # 캐시에 없으면 메타데이터에서 가져오기
            display_name = get_db_display_name(db_index)
        
        elapsed_time = time.time() - start_time
        print(f"DB 변경 완료 - '{display_name}' (소요 시간: {elapsed_time:.4f}초)")
        
        return jsonify({
            'status': 'success', 
            'message': f'{display_name}로 변경되었습니다.',
            'elapsed_time': elapsed_time
        })
    except Exception as e:
        print(f"DB 변경 오류: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': f'DB 변경 중 오류: {str(e)}'
        }), 500

@app.route('/clear', methods=['POST'])
def clear_conversation():
    session['messages'] = []
    session['thread_id'] = str(uuid.uuid4())
    return jsonify({'status': 'success'})

# app.py 파일의 add_message 함수를 다음과 같이 수정하세요
def add_message(role, content):
    if 'messages' not in session:
        session['messages'] = []
    
    # 새 메시지 추가
    session['messages'].append({'role': role, 'content': content})
    
    # 메시지가 10개를 초과하면 가장 오래된 메시지 제거 (FIFO)
    if len(session['messages']) > 20:  # 10개의 대화 쌍(사용자+AI) = 20개 메시지
        session['messages'] = session['messages'][-20:]
    
    session.modified = True

# app.py 파일에서 get_message_history 함수를 다음과 같이 수정하세요

def get_message_history():
    ret = []
    for chat_message in session.get('messages', []):
        if chat_message['role'] == 'user':
            ret.append(HumanMessage(content=chat_message['content']))
        else:
            ret.append(AIMessage(content=chat_message['content']))
    return ret

# app.py 파일의 run_graph 함수를 다음과 같이 수정하세요

# app.py 파일의 run_graph 함수를 다음과 같이 수정하세요

def run_graph(graph, query, thread_id):
    from states import GraphState
    from langchain_core.runnables import RunnableConfig
    
    config = RunnableConfig(recursion_limit=30, configurable={"thread_id": thread_id})
    
    # 대화 히스토리 가져오기
    chat_history = get_message_history()
    
    # 질문 입력 (대화 히스토리 포함)
    inputs = GraphState(
        question=query, 
        documents=[],  # 초기에는 빈 문서 리스트로 설정
        generation="",  # 초기 생성 텍스트는 빈 문자열
        chat_history=chat_history  # 대화 히스토리 추가
    )
    
    # 큐가 없으면 생성
    if thread_id not in progress_queues:
        progress_queues[thread_id] = queue.Queue()
    
    q = progress_queues[thread_id]
    
    # 처리 단계별 메시지 정의
    actions = {
        "retrieve": "🔍 문서를 조회하는 중입니다.",
        "grade_documents": "👀 조회한 문서 중 중요한 내용을 추려내는 중입니다.",
        "rag_answer": "🔥 문서를 기반으로 답변을 생성하는 중입니다.",
        "general_answer": "🔥 문서를 기반으로 답변을 생성하는 중입니다.",
        "web_search": "🛜 웹 검색을 진행하는 중입니다.",
    }
    
    # 이미 처리한 단계를 기록하기 위한 세트
    processed_steps = set()
    
    # 스트리밍 처리를 위한 래퍼 함수
    def process_steps(output):
        for key in output:
            if key in actions and key not in processed_steps:
                # 새로운 단계를 처리할 때만 메시지 전송
                processed_steps.add(key)
                q.put(actions[key])
        return output
    
    try:
        # 스트리밍 콜백 함수를 그래프에 적용
        for output in graph.stream(inputs, config=config):
            process_steps(output)
        
        # 처리 완료 신호
        q.put("DONE")
        
        # 최종 결과 반환
        return graph.invoke(inputs, config=config)
    except Exception as e:
        # 오류 발생 시 큐에 완료 신호 전송 후 예외 다시 발생
        q.put("DONE")
        raise e

    
if __name__ == '__main__':
    # 초기화가 한 번만 실행되도록 합니다
    # print("앱 초기화 - 벡터 DB 및 그래프 사전 로드 시작")
    # init_app()
    # print("앱 초기화 - 벡터 DB 및 그래프 사전 로드 완료")
    # print(f"로드된 DB 캐시 키 목록: {list(db_cache.keys())}")

    # # 사전 로드된 DB 수 확인 및 로그
    # db_with_graphs = sum(1 for db in db_cache.values() if db.get('graph') is not None)
    # print(f"그래프가 생성된 DB 수: {db_with_graphs}/{len(db_cache)}")
    
    # debug=False로 설정하여 중복 로드 방지
    app.run(debug=False, host='0.0.0.0', port=5000)