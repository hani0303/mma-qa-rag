import os
import shutil
import urllib.parse
import json
import datetime
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from langchain_community.document_loaders import (
    PDFPlumberLoader, TextLoader, CSVLoader, 
    Docx2txtLoader, UnstructuredExcelLoader, 
    UnstructuredPowerPointLoader, UnstructuredHTMLLoader,
    UnstructuredImageLoader, UnstructuredWordDocumentLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from LlamaParseLoader import LlamaParseLoader

# Define allowed file extensions and upload folder
ALLOWED_EXTENSIONS = {
    'pdf', 'txt', 'csv', 'doc', 'docx', 'hwp', 
    'xlsx', 'xls', 'ppt', 'pptx', 'html', 'htm',
    'jpg', 'jpeg', 'png', 'gif', 'bmp'
}
UPLOAD_FOLDER = 'data'
VECTOR_DB_FOLDER = 'LANGCHAIN_DB_INDEX_'
DB_METADATA_FILE = 'db_metadata.json'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_loader_for_file(file_path, pdf_loader_type='pdfplumber'):
    """파일 확장자에 맞는 로더를 반환합니다."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        if pdf_loader_type == 'llamaparse':
            # LlamaParseLoader 사용
            parsing_instructions = """This document is an official document from the Military Manpower Administration of the Republic of Korea, related to military recruitment regulations, guidelines, and laws.
            It is crucial that tables are accurately parsed and extracted as text, as they contain important information.
            Please ensure all content is processed in Korean.
            """
            return LlamaParseLoader([file_path], parsing_instructions=parsing_instructions)
        else:
            # 기본 PDFPlumberLoader 사용
            return PDFPlumberLoader(file_path)
    elif ext == '.txt':
        return TextLoader(file_path, encoding='utf-8')  # UTF-8 인코딩 명시
    # 나머지 코드는 동일하게 유지
    elif ext == '.csv':
        return CSVLoader(file_path)
    elif ext in ['.doc', '.docx']:
        return Docx2txtLoader(file_path)
    elif ext in ['.xls', '.xlsx']:
        return UnstructuredExcelLoader(file_path)
    elif ext in ['.ppt', '.pptx']:
        return UnstructuredPowerPointLoader(file_path)
    elif ext in ['.html', '.htm']:
        return UnstructuredHTMLLoader(file_path)
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        return UnstructuredImageLoader(file_path)
    elif ext == '.hwp':
        # HWP 파일 처리를 위해 UnstructuredWordDocumentLoader 사용 시도
        return UnstructuredWordDocumentLoader(file_path)
    else:
        raise ValueError(f"지원되지 않는 파일 형식입니다: {ext}")

def preserve_filename(filename):
    """
    파일명에 한글이나 공백을 보존하면서 안전하게 저장할 수 있는 형태로 변환합니다.
    """
    # URL 인코딩으로 특수문자 처리
    filename_for_storage = urllib.parse.quote(filename)
    return filename_for_storage

def restore_filename(encoded_filename):
    """
    저장된 인코딩된 파일명을 원래의 형태로 복원합니다.
    """
    return urllib.parse.unquote(encoded_filename)

def load_db_metadata():
    """DB 메타데이터 파일을 로드합니다."""
    if os.path.exists(DB_METADATA_FILE):
        try:
            with open(DB_METADATA_FILE, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
                # 메타데이터 구조 검증 및 복구
                if '_categories' not in metadata:
                    metadata['_categories'] = []
                
                # DB 항목마다 필수 필드 확인 및 추가
                for key, value in list(metadata.items()):
                    if key != '_categories' and isinstance(value, dict):
                        # display_name이 없으면 추가
                        if 'display_name' not in value or not value['display_name']:
                            value['display_name'] = key.replace(VECTOR_DB_FOLDER, '')
                        
                        # category가 없으면 추가
                        if 'category' not in value or not value['category']:
                            value['category'] = '기타'
                
                return metadata
        except Exception as e:
            print(f"메타데이터 파일 로드 중 오류: {e}")
            # 파일 손상 시 새 메타데이터 생성
            return {'_categories': ['기타']}
    return {'_categories': ['기타']}  # 파일이 없으면 기본값 반환

def save_db_metadata(metadata):
    """DB 메타데이터 파일을 저장합니다."""
    try:
        with open(DB_METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"메타데이터 파일 저장 중 오류: {e}")

def get_db_display_name(db_id):
    """DB ID에 해당하는 표시 이름을 반환합니다."""
    metadata = load_db_metadata()
    return metadata.get(db_id, {}).get('display_name', db_id.replace(VECTOR_DB_FOLDER, ''))

def get_all_categories():
    """모든 카테고리 목록을 가져옵니다."""
    metadata = load_db_metadata()
    categories = set()
    
    # 1. 모든 DB에서 사용중인 카테고리 수집
    for key, value in metadata.items():
        if key != '_categories' and isinstance(value, dict) and 'category' in value:
            if value['category'] and isinstance(value['category'], str):
                categories.add(value['category'])
    
    # 2. 저장된 카테고리 목록 추가
    if '_categories' in metadata and isinstance(metadata['_categories'], list):
        for category in metadata['_categories']:
            if category and isinstance(category, str):
                categories.add(category)
    
    # 3. 기본 카테고리 추가
    categories.add('기타')
    
    return sorted(list(categories))


def setup_document_manager(app):
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    @app.route('/document_manager')
    def document_manager():
        # Get list of uploaded documents
        documents = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            # 파일 확장자 확인
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
                # 실제 화면에 표시할 때는 디코딩된 원본 파일명 사용
                original_filename = restore_filename(filename)
                documents.append({
                    'storage_name': filename,
                    'display_name': original_filename
                })
        
        # Get list of vector DBs with display names
        vector_dbs = []
        metadata = load_db_metadata()
        
        for folder in os.listdir():
            if folder.startswith(VECTOR_DB_FOLDER):
                # DB ID에서 접두어 제거
                db_id = folder
                # 메타데이터에서 표시 이름 가져오기
                display_name = metadata.get(db_id, {}).get('display_name', folder[len(VECTOR_DB_FOLDER):])
                if not display_name:  # 빈 이름인 경우 기본값 설정
                    display_name = "기본 DB"
                
                # 카테고리 정보 가져오기
                category = metadata.get(db_id, {}).get('category', '기타')
                
                vector_dbs.append({
                    'id': db_id,
                    'name': display_name,
                    'category': category
                })
        
        # 모든 카테고리 목록 가져오기
        categories = get_all_categories()
        if '기타' not in categories:
            categories.append('기타')
        
        return render_template('document_manager.html', 
                              documents=documents, 
                              vector_dbs=vector_dbs, 
                              categories=categories)
    


    @app.route('/add_documents_to_db', methods=['POST'])
    def add_documents_to_db():
        data = request.json
        db_id = data.get('db_id')
        storage_filenames = data.get('storage_filenames', [])
        custom_names = data.get('custom_names', {})  # 새로 추가: 사용자 지정 문서명
        
        if not db_id or not storage_filenames:
            return jsonify({'status': 'error', 'message': 'DB ID 또는 파일이 제공되지 않았습니다.'}), 400
        
        try:
            # 벡터 DB가 존재하는지 확인
            if not os.path.exists(db_id) or not os.path.isdir(db_id):
                return jsonify({'status': 'error', 'message': '벡터 DB를 찾을 수 없습니다.'}), 404
            
            # 메타데이터에서 청크 설정 가져오기
            metadata = load_db_metadata()
            db_info = metadata.get(db_id, {})
            chunk_size = db_info.get('chunk_size', 300)
            chunk_overlap = db_info.get('chunk_overlap', 50)
            
            # 모든 문서를 로드합니다
            all_documents = []
            for storage_filename in storage_filenames:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], storage_filename)
                
                if not os.path.exists(file_path):
                    return jsonify({'status': 'error', 'message': f'파일을 찾을 수 없습니다: {restore_filename(storage_filename)}'}), 404
                
                try:
                    # 파일 형식에 맞는 로더 가져오기
                    loader = get_loader_for_file(file_path)
                    documents = loader.load()
                    
                    # 사용자 지정 문서명이 있으면 메타데이터에 추가
                    original_filename = restore_filename(storage_filename)
                    custom_name = custom_names.get(storage_filename, original_filename)
                    
                    for doc in documents:
                        # 기존 메타데이터 유지하면서 사용자 지정 문서명 추가
                        doc.metadata['custom_name'] = custom_name
                        doc.metadata['original_filename'] = original_filename
                    
                    all_documents.extend(documents)
                    print(f"파일 '{storage_filename}' 로드 완료: {len(documents)}개 문서")
                except Exception as e:
                    print(f"파일 '{storage_filename}' 로드 오류: {str(e)}")
                    return jsonify({'status': 'error', 'message': f"파일 '{restore_filename(storage_filename)}' 로드 중 오류: {str(e)}"}), 500
            
            if not all_documents:
                return jsonify({'status': 'error', 'message': '로드된 문서가 없습니다.'}), 400
            
            # 문서 분할
            print(f"[청크 설정] 크기: {chunk_size}자, 오버랩: {chunk_overlap}자")
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            split_docs = text_splitter.split_documents(all_documents)
            print(f"[문서 분할 완료] 총 {len(all_documents)}개 문서에서 {len(split_docs)}개 청크 생성됨")
            
            # 기존 벡터스토어 로드
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vectorstore = FAISS.load_local(db_id, embeddings, allow_dangerous_deserialization=True)
            
            # 새 문서 추가
            vectorstore.add_documents(split_docs)
            
            # 업데이트된 벡터스토어 저장
            vectorstore.save_local(db_id)
            
            # 메타데이터 업데이트 (마지막 수정 시간)
            if db_id in metadata:
                metadata[db_id]['last_updated'] = datetime.datetime.now().isoformat()
                metadata[db_id]['added_documents'] = metadata[db_id].get('added_documents', 0) + len(storage_filenames)
            save_db_metadata(metadata)
            
            return jsonify({
                'status': 'success', 
                'message': f'벡터 DB에 {len(storage_filenames)}개 문서 추가 완료!',
                'document_count': len(all_documents),
                'chunk_count': len(split_docs)
            })
        except Exception as e:
            print(f"문서 추가 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'status': 'error', 'message': f'문서 추가 중 오류: {str(e)}'}), 500

    @app.route('/remove_documents_from_db', methods=['POST'])
    def remove_documents_from_db():
        data = request.json
        db_id = data.get('db_id')
        document_ids = data.get('document_ids', [])
        
        if not db_id or not document_ids:
            return jsonify({'status': 'error', 'message': 'DB ID 또는 문서 ID가 제공되지 않았습니다.'}), 400
        
        try:
            # 벡터 DB가 존재하는지 확인
            if not os.path.exists(db_id) or not os.path.isdir(db_id):
                return jsonify({'status': 'error', 'message': '벡터 DB를 찾을 수 없습니다.'}), 404
            
            # 메타데이터 가져오기
            metadata = load_db_metadata()
            db_info = metadata.get(db_id, {})
            display_name = db_info.get('display_name', db_id.replace(VECTOR_DB_FOLDER, ''))
            
            # 여기서는 실제로 문서를 삭제하는 대신, 전체 DB를 다시 생성하는 방식으로 구현합니다.
            # (FAISS는 문서 삭제를 직접적으로 지원하지 않기 때문)
            # 실제 구현에서는 DB를 백업하고 새로 생성하는 로직이 필요합니다.
            
            # 간단한 메시지 반환 (시연용)
            return jsonify({
                'status': 'success', 
                'message': f'벡터 DB "{display_name}"에서 {len(document_ids)}개 문서 삭제 요청 처리됨',
                'note': '문서 삭제 기능은 현재 개발 중입니다.'
            })
        except Exception as e:
            print(f"문서 삭제 중 오류: {str(e)}")
            return jsonify({'status': 'error', 'message': f'문서 삭제 중 오류: {str(e)}'}), 500

    @app.route('/get_db_info', methods=['POST'])
    def get_db_info():
        data = request.json
        db_id = data.get('db_id')
        
        if not db_id:
            return jsonify({'status': 'error', 'message': 'DB ID가 제공되지 않았습니다.'}), 400
        
        try:
            # 벡터 DB가 존재하는지 확인
            if not os.path.exists(db_id) or not os.path.isdir(db_id):
                return jsonify({'status': 'error', 'message': '벡터 DB를 찾을 수 없습니다.'}), 404
            
            # 메타데이터 가져오기
            metadata = load_db_metadata()
            db_info = metadata.get(db_id, {})
            
            # DB 정보 반환
            return jsonify({
                'status': 'success',
                'db_info': {
                    'id': db_id,
                    'name': db_info.get('display_name', db_id.replace(VECTOR_DB_FOLDER, '')),
                    'category': db_info.get('category', '기타'),
                    'chunk_size': db_info.get('chunk_size', 300),
                    'chunk_overlap': db_info.get('chunk_overlap', 50),
                    'created_at': db_info.get('created_at', ''),
                    'last_updated': db_info.get('last_updated', db_info.get('created_at', '')),
                    'document_count': db_info.get('added_documents', 0)
                }
            })
        except Exception as e:
            print(f"DB 정보 조회 중 오류: {str(e)}")
            return jsonify({'status': 'error', 'message': f'DB 정보 조회 중 오류: {str(e)}'}), 500
        
    @app.route('/upload_documents', methods=['POST'])
    def upload_documents():
        # 파일이 제공되지 않았다면
        if 'documents[]' not in request.files:
            return jsonify({'status': 'error', 'message': '파일이 제공되지 않았습니다.'}), 400
        
        files = request.files.getlist('documents[]')
        
        # 파일이 선택되지 않았다면
        if not files or files[0].filename == '':
            return jsonify({'status': 'error', 'message': '선택된 파일이 없습니다.'}), 400
        
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                # 원본 파일명 보존
                original_filename = file.filename
                # 저장용 파일명 (인코딩된 형태)
                storage_filename = preserve_filename(original_filename)
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], storage_filename)
                file.save(file_path)
                uploaded_files.append({
                    'original_name': original_filename,
                    'storage_name': storage_filename
                })
        
        if uploaded_files:
            return jsonify({
                'status': 'success', 
                'message': f'{len(uploaded_files)}개 파일 업로드 완료!', 
                'files': uploaded_files
            })
        else:
            return jsonify({'status': 'error', 'message': '허용되지 않는 파일 형식입니다.'}), 400
    
    @app.route('/delete_document', methods=['POST'])
    def delete_document():
        data = request.json
        storage_filename = data.get('storage_filename')
        
        if not storage_filename:
            return jsonify({'status': 'error', 'message': '파일명이 제공되지 않았습니다.'}), 400
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], storage_filename)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return jsonify({'status': 'success', 'message': f'{restore_filename(storage_filename)} 삭제 완료!'})
            else:
                return jsonify({'status': 'error', 'message': '파일을 찾을 수 없습니다.'}), 404
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'파일 삭제 중 오류: {str(e)}'}), 500
    
    @app.route('/get_categories', methods=['GET'])
    def get_categories():
        """모든 카테고리 목록을 반환합니다."""
        categories = get_all_categories()
        if '기타' not in categories:
            categories.append('기타')
        return jsonify({'status': 'success', 'categories': categories})
    
    @app.route('/add_category', methods=['POST'])
    def add_category():
        """새 카테고리를 추가합니다."""
        data = request.json
        category_name = data.get('category_name', '').strip()
        
        if not category_name:
            return jsonify({'status': 'error', 'message': '카테고리 이름이 제공되지 않았습니다.'}), 400
        
        # 카테고리 목록 가져오기
        categories = get_all_categories()
        
        # 이미 존재하는 카테고리인지 확인
        if category_name in categories:
            return jsonify({'status': 'error', 'message': f'카테고리 "{category_name}"이(가) 이미 존재합니다.'}), 400
        
        try:
            # 메타데이터 로드
            metadata = load_db_metadata()
            
            # 카테고리 정보를 저장할 특별한 키 추가
            if '_categories' not in metadata:
                metadata['_categories'] = []
            
            # 새 카테고리 추가
            if category_name not in metadata['_categories']:
                metadata['_categories'].append(category_name)
            
            # 메타데이터 파일 저장
            save_db_metadata(metadata)
            
            # 업데이트된 카테고리 목록 반환
            all_categories = get_all_categories()
            if '기타' not in all_categories:
                all_categories.append('기타')
            
            return jsonify({
                'status': 'success', 
                'message': f'카테고리 "{category_name}" 추가 완료!', 
                'categories': sorted(all_categories)
            })
            
        except Exception as e:
            print(f"카테고리 추가 중 오류: {str(e)}")
            return jsonify({'status': 'error', 'message': f'카테고리 추가 중 오류: {str(e)}'}), 500
    
    
    @app.route('/create_vector_db_from_multiple', methods=['POST'])
    def create_vector_db_from_multiple():
        data = request.json
        storage_filenames = data.get('storage_filenames', [])
        db_name = data.get('db_name')
        document_name = data.get('document_name', '')  # 문서 이름 추가
        category = data.get('category', '기타')
        pdf_loader = data.get('pdf_loader', 'pdfplumber')
        
        # 청크 크기와 오버랩 크기 파라미터 추가
        chunk_size = data.get('chunk_size', 300)
        chunk_overlap = data.get('chunk_overlap', 50)
        
        # 숫자형으로 변환 (문자열로 전송될 경우 대비)
        try:
            chunk_size = int(chunk_size)
            chunk_overlap = int(chunk_overlap)
        except (ValueError, TypeError):
            chunk_size = 300
            chunk_overlap = 50
        
        # 유효성 검사: 최소값 설정
        if chunk_size < 100:
            chunk_size = 100
        if chunk_overlap < 0:
            chunk_overlap = 0
        if chunk_overlap >= chunk_size:
            chunk_overlap = chunk_size // 2
        
        if not storage_filenames or not db_name:
            return jsonify({'status': 'error', 'message': '파일명 또는 DB명이 제공되지 않았습니다.'}), 400
        
        try:
            # 모든 문서를 로드합니다
            all_documents = []
            for storage_filename in storage_filenames:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], storage_filename)
                
                if not os.path.exists(file_path):
                    return jsonify({'status': 'error', 'message': f'파일을 찾을 수 없습니다: {restore_filename(storage_filename)}'}), 404
                
                try:
                    # 파일 형식에 맞는 로더 가져오기 (PDF 로더 타입 전달)
                    loader = get_loader_for_file(file_path, pdf_loader)
                    documents = loader.load()
                    
                    # 문서 이름이 제공된 경우 메타데이터에 추가
                    if document_name:
                        for doc in documents:
                            doc.metadata['custom_name'] = document_name
                            # 원본 파일명도 보존
                            doc.metadata['original_filename'] = restore_filename(storage_filename)
                            
                    all_documents.extend(documents)
                    print(f"파일 '{storage_filename}' 로드 완료: {len(documents)}개 문서")
                except Exception as e:
                    print(f"파일 '{storage_filename}' 로드 오류: {str(e)}")
                    return jsonify({'status': 'error', 'message': f"파일 '{restore_filename(storage_filename)}' 로드 중 오류: {str(e)}"}), 500
            
            if not all_documents:
                return jsonify({'status': 'error', 'message': '로드된 문서가 없습니다.'}), 400
            
            print(f"총 {len(all_documents)}개 문서 로드 완료")
            
            # 문서 분할 - 사용자 지정 청크 크기와 오버랩 사용
            print(f"[청크 설정] 크기: {chunk_size}자, 오버랩: {chunk_overlap}자")
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            split_docs = text_splitter.split_documents(all_documents)
            print(f"[문서 분할 완료] 총 {len(all_documents)}개 문서에서 {len(split_docs)}개 청크 생성됨")

            # 벡터스토어 생성
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vectorstore = FAISS.from_documents(documents=split_docs, embedding=embeddings)
            
            # 벡터 DB ID 생성 (접두어 + DB 이름 인코딩)
            now = datetime.datetime.now()
            system_db_id = f"db_{now.strftime('%Y%m%d%H%M%S')}"  # 예: db_20250417123045
            db_id = f"{VECTOR_DB_FOLDER}{system_db_id}"
                        
            # 벡터 DB 저장
            vectorstore.save_local(db_id)
            print(f"벡터 DB '{db_name}' 저장 완료")
            
            # 메타데이터에 표시 이름과 청크 설정 저장
            metadata = load_db_metadata()
            metadata[db_id] = {
                'display_name': db_name,  # 원본 한글 이름을 표시 이름으로 저장
                'created_at': datetime.datetime.now().isoformat(),
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'category': category,  # 카테고리 정보 추가
                'document_name': document_name  # 문서 이름 저장
            }
            save_db_metadata(metadata)
            
            return jsonify({
                'status': 'success', 
                'message': f'벡터 DB "{db_name}" 생성 완료!',
                'db_name': db_name,
                'db_id': db_id,
                'document_count': len(all_documents),
                'chunk_count': len(split_docs),
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'category': category,
                'document_name': document_name or '원본 파일명'
            })
        except Exception as e:
            print(f"벡터 DB 생성 중 오류: {str(e)}")
            return jsonify({'status': 'error', 'message': f'벡터 DB 생성 중 오류: {str(e)}'}), 500
    
    
    
    @app.route('/delete_vector_db', methods=['POST'])
    def delete_vector_db():
        data = request.json
        db_id = data.get('db_id')
        
        if not db_id:
            return jsonify({'status': 'error', 'message': 'DB ID가 제공되지 않았습니다.'}), 400
        
        try:
            if os.path.exists(db_id) and os.path.isdir(db_id):
                # 메타데이터에서 삭제
                metadata = load_db_metadata()
                if db_id in metadata:
                    # 표시 이름 가져오기
                    display_name = metadata[db_id].get('display_name', db_id.replace(VECTOR_DB_FOLDER, ''))
                    del metadata[db_id]
                    save_db_metadata(metadata)
                else:
                    display_name = db_id.replace(VECTOR_DB_FOLDER, '')
                
                # 벡터 DB 디렉토리 삭제
                shutil.rmtree(db_id)
                return jsonify({'status': 'success', 'message': f'벡터 DB "{display_name}" 삭제 완료!'})
            else:
                return jsonify({'status': 'error', 'message': '벡터 DB를 찾을 수 없습니다.'}), 404
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'벡터 DB 삭제 중 오류: {str(e)}'}), 500
    
    @app.route('/delete_category', methods=['POST'])
    def delete_category():
        """카테고리를 삭제합니다."""
        data = request.json
        category_name = data.get('category_name', '').strip()
        
        if not category_name:
            return jsonify({'status': 'error', 'message': '카테고리 이름이 제공되지 않았습니다.'}), 400
        
        try:
            metadata = load_db_metadata()
            
            # 해당 카테고리를 사용하는 모든 DB를 '기타'로 변경
            for db_id, db_info in metadata.items():
                if isinstance(db_info, dict) and db_info.get('category') == category_name:
                    metadata[db_id]['category'] = '기타'
            
            # '_categories' 배열에서 카테고리 제거 - 이 부분이 추가되어야 함
            if '_categories' in metadata and isinstance(metadata['_categories'], list):
                if category_name in metadata['_categories']:
                    metadata['_categories'].remove(category_name)
            
            save_db_metadata(metadata)
            
            # 남은 카테고리 목록 반환
            categories = get_all_categories()
            if '기타' not in categories:
                categories.append('기타')
            
            return jsonify({
                'status': 'success', 
                'message': f'카테고리 "{category_name}" 삭제 완료!',
                'categories': sorted(categories)
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'카테고리 삭제 중 오류: {str(e)}'}), 500

    
    @app.route('/update_db_category', methods=['POST'])
    def update_db_category():
        data = request.json
        db_id = data.get('db_id')
        new_category = data.get('category')
        
        if not db_id or not new_category:
            return jsonify({'status': 'error', 'message': 'DB ID 또는 카테고리가 제공되지 않았습니다.'}), 400
        
        try:
            metadata = load_db_metadata()
            
            # DB ID가 존재하는지 확인
            if db_id in metadata:
                # 기존 카테고리 저장
                old_category = metadata[db_id].get('category', '기타')
                
                # 새 카테고리 저장
                metadata[db_id]['category'] = new_category
                
                # 카테고리 목록 업데이트
                if '_categories' not in metadata:
                    metadata['_categories'] = []
                
                # 새 카테고리가 목록에 없으면 추가
                if new_category not in metadata['_categories'] and new_category != '기타':
                    metadata['_categories'].append(new_category)
                
                # 메타데이터 저장
                save_db_metadata(metadata)
                
                return jsonify({
                    'status': 'success', 
                    'message': f'카테고리가 "{new_category}"로 변경되었습니다.', 
                    'db_id': db_id, 
                    'old_category': old_category,
                    'new_category': new_category
                })
            else:
                # DB ID가 메타데이터에 없으면 새로 추가
                metadata[db_id] = {
                    'display_name': db_id.replace(VECTOR_DB_FOLDER, ''),
                    'category': new_category,
                    'created_at': datetime.datetime.now().isoformat()
                }
                
                # 새 카테고리가 목록에 없으면 추가
                if '_categories' not in metadata:
                    metadata['_categories'] = []
                if new_category not in metadata['_categories'] and new_category != '기타':
                    metadata['_categories'].append(new_category)
                
                # 메타데이터 저장
                save_db_metadata(metadata)
                
                return jsonify({
                    'status': 'success', 
                    'message': f'DB가 추가되고 카테고리가 "{new_category}"로 설정되었습니다.', 
                    'db_id': db_id, 
                    'new_category': new_category
                })
        except Exception as e:
            print(f"카테고리 변경 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': 'error', 
                'message': f'카테고리 변경 중 오류: {str(e)}'
            }), 500
            
            
    @app.route('/rename_category', methods=['POST'])
    def rename_category():
        """카테고리 이름을 변경합니다."""
        data = request.json
        old_name = data.get('old_name', '').strip()
        new_name = data.get('new_name', '').strip()
        
        if not old_name or not new_name:
            return jsonify({'status': 'error', 'message': '기존 카테고리 이름과 새 이름이 모두 필요합니다.'}), 400
        
        try:
            metadata = load_db_metadata()
            
            # 해당 카테고리를 사용하는 모든 DB의 카테고리 이름 변경
            for db_id, db_info in metadata.items():
                if isinstance(db_info, dict) and db_info.get('category') == old_name:
                    metadata[db_id]['category'] = new_name
            
            # '_categories' 배열에서 카테고리 이름 변경 - 이 부분이 추가되어야 함
            if '_categories' in metadata and isinstance(metadata['_categories'], list):
                if old_name in metadata['_categories']:
                    index = metadata['_categories'].index(old_name)
                    metadata['_categories'][index] = new_name
            
            save_db_metadata(metadata)
            
            # 업데이트된 카테고리 목록 반환
            categories = get_all_categories()
            if '기타' not in categories:
                categories.append('기타')
            
            return jsonify({
                'status': 'success', 
                'message': f'카테고리 "{old_name}"이(가) "{new_name}"으로 변경되었습니다.',
                'categories': sorted(categories)
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'카테고리 이름 변경 중 오류: {str(e)}'}), 500
    
    @app.route('/get_vector_dbs', methods=['GET'])
    def get_vector_dbs():
        vector_dbs = []
        metadata = load_db_metadata()
        
        # 실제 존재하는 벡터 DB 디렉토리 확인
        existing_folders = [folder for folder in os.listdir() if folder.startswith(VECTOR_DB_FOLDER) and os.path.isdir(folder)]
        
        # 메타데이터와 실제 폴더 동기화 - 메타데이터 업데이트 필요 여부
        metadata_updated = False
        
        for folder in existing_folders:
            # 메타데이터에서 표시 이름 가져오기
            db_info = metadata.get(folder, {})
            
            # 표시 이름 없으면 폴더명 사용
            display_name = db_info.get('display_name')
            if not display_name:
                display_name = folder[len(VECTOR_DB_FOLDER):]
                # 메타데이터 업데이트
                if folder in metadata:
                    metadata[folder]['display_name'] = display_name
                    metadata_updated = True
                else:
                    metadata[folder] = {'display_name': display_name, 'category': '기타', 'created_at': datetime.datetime.now().isoformat()}
                    metadata_updated = True
            
            # 카테고리 정보 가져오기 (없으면 기타)
            category = db_info.get('category', '기타')
            if not category:
                category = '기타'
                # 메타데이터 업데이트
                if folder in metadata:
                    metadata[folder]['category'] = category
                    metadata_updated = True
            
            vector_dbs.append({
                'id': folder,
                'name': display_name,
                'category': category
            })
        
        # 메타데이터에 있지만 실제로는 없는 폴더 처리
        for key in list(metadata.keys()):
            if key != '_categories' and key.startswith(VECTOR_DB_FOLDER) and key not in existing_folders:
                # 옵션 1: 메타데이터에서 제거 (정리)
                # del metadata[key]
                # metadata_updated = True
                
                # 옵션 2: 유지하되 표시하지 않음 (위의 vector_dbs에 포함되지 않음)
                pass
        
        # 메타데이터 변경사항 있으면 저장
        if metadata_updated:
            save_db_metadata(metadata)
        
        # 카테고리별로 그룹화
        categorized_dbs = {}
        for db in vector_dbs:
            category = db['category']
            if category not in categorized_dbs:
                categorized_dbs[category] = []
            categorized_dbs[category].append(db)
        
        return jsonify({'status': 'success', 'vector_dbs': vector_dbs, 'categorized_dbs': categorized_dbs})
    
    @app.route('/get_db_documents', methods=['POST'])
    def get_db_documents():
        data = request.json
        db_id = data.get('db_id')
        
        if not db_id:
            return jsonify({'status': 'error', 'message': 'DB ID가 제공되지 않았습니다.'}), 400
        
        try:
            # 벡터 DB가 존재하는지 확인
            if not os.path.exists(db_id) or not os.path.isdir(db_id):
                return jsonify({'status': 'error', 'message': '벡터 DB를 찾을 수 없습니다.'}), 404
            
            # 해당 DB에서 임베딩 불러오기
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vectorstore = FAISS.load_local(db_id, embeddings, allow_dangerous_deserialization=True)
            
            # 문서 목록 가져오기 (FAISS에서는 직접적으로 문서 메타데이터에 접근 가능)
            documents = []
            if hasattr(vectorstore, 'docstore') and hasattr(vectorstore.docstore, '_dict'):
                for doc_id, doc in vectorstore.docstore._dict.items():
                    # 소스 문서 경로에서 파일명만 추출
                    source = doc.metadata.get('source', '알 수 없음')
                    filename = os.path.basename(source) if source else '알 수 없음'
                    
                    # URL 디코딩하여 원본 파일명 가져오기
                    original_filename = urllib.parse.unquote(filename)
                    
                    # 사용자 지정 문서명 가져오기
                    custom_name = doc.metadata.get('custom_name', original_filename)
                    
                    # 내용 일부만 표시 (최대 50자)
                    content_preview = doc.page_content[:50] + '...' if len(doc.page_content) > 50 else doc.page_content
                    
                    # 메타데이터에서 필요한 정보 추출
                    metadata = {}
                    for key, value in doc.metadata.items():
                        if key not in ['source'] and value:  # source는 이미 별도로 처리했으므로 제외
                            metadata[key] = value
                    
                    documents.append({
                        'id': doc_id,
                        'source': source,  # 전체 경로는 내부적으로 사용
                        'filename': filename,  # 화면에 표시할 인코딩된 파일명
                        'original_filename': original_filename,  # 디코딩된 원본 파일명
                        'custom_name': custom_name,  # 사용자 지정 문서명
                        'content': content_preview,  # 미리보기용 짧은 내용
                        'metadata': metadata  # 추가 메타데이터
                    })
            
            return jsonify({
                'status': 'success',
                'documents': documents,
                'count': len(documents)
            })
        except Exception as e:
            print(f"문서 목록 조회 중 오류: {str(e)}")
            return jsonify({'status': 'error', 'message': f'문서 목록 조회 중 오류: {str(e)}'}), 500
            
        
    @app.route('/remove_document_from_db', methods=['POST'])
    def remove_document_from_db():
        data = request.json
        db_id = data.get('db_id')
        doc_id = data.get('doc_id')
        
        if not db_id or not doc_id:
            return jsonify({'status': 'error', 'message': 'DB ID 또는 문서 ID가 제공되지 않았습니다.'}), 400
        
        try:
            # 벡터 DB가 존재하는지 확인
            if not os.path.exists(db_id) or not os.path.isdir(db_id):
                return jsonify({'status': 'error', 'message': '벡터 DB를 찾을 수 없습니다.'}), 404
            
            # 해당 DB에서 임베딩 불러오기
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vectorstore = FAISS.load_local(db_id, embeddings, allow_dangerous_deserialization=True)
            
            # 문서 삭제 (FAISS는 문서 삭제를 직접 지원하지 않아 우회적인 방법 사용)
            if hasattr(vectorstore, 'docstore') and hasattr(vectorstore.docstore, '_dict'):
                if doc_id in vectorstore.docstore._dict:
                    # 문서 메타데이터와 임시 정보 저장
                    deleted_doc = vectorstore.docstore._dict[doc_id]
                    
                    # 문서 삭제
                    del vectorstore.docstore._dict[doc_id]
                    
                    # 문서 ID를 인덱스 매핑에서도 제거
                    if hasattr(vectorstore, 'index_to_docstore_id'):
                        for idx, d_id in list(vectorstore.index_to_docstore_id.items()):
                            if d_id == doc_id:
                                del vectorstore.index_to_docstore_id[idx]
                    
                    # 벡터스토어 다시 저장
                    vectorstore.save_local(db_id)
                    
                    # 메타데이터 업데이트
                    metadata = load_db_metadata()
                    if db_id in metadata:
                        metadata[db_id]['last_updated'] = datetime.datetime.now().isoformat()
                        
                        # 문서 수 업데이트 (있는 경우)
                        if 'document_count' in metadata[db_id]:
                            metadata[db_id]['document_count'] = max(0, metadata[db_id].get('document_count', 1) - 1)
                        
                        save_db_metadata(metadata)
                    
                    return jsonify({
                        'status': 'success', 
                        'message': f'문서가 벡터 DB에서 성공적으로 삭제되었습니다.',
                        'deleted_doc': {
                            'id': doc_id,
                            'source': deleted_doc.metadata.get('source', '알 수 없음')
                        }
                    })
                else:
                    return jsonify({'status': 'error', 'message': '지정된 ID의 문서를 찾을 수 없습니다.'}), 404
            else:
                return jsonify({'status': 'error', 'message': '벡터 DB 문서 저장소에 접근할 수 없습니다.'}), 500
        except Exception as e:
            print(f"문서 삭제 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'status': 'error', 'message': f'문서 삭제 중 오류: {str(e)}'}), 500
    
    
    @app.route('/remove_documents_by_source', methods=['POST'])
    def remove_documents_by_source():
        data = request.json
        db_id = data.get('db_id')
        source = data.get('source')
        
        if not db_id or not source:
            return jsonify({'status': 'error', 'message': 'DB ID 또는 문서 출처가 제공되지 않았습니다.'}), 400
        
        try:
            # 벡터 DB가 존재하는지 확인
            if not os.path.exists(db_id) or not os.path.isdir(db_id):
                return jsonify({'status': 'error', 'message': '벡터 DB를 찾을 수 없습니다.'}), 404
            
            # 해당 DB에서 임베딩 불러오기
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vectorstore = FAISS.load_local(db_id, embeddings, allow_dangerous_deserialization=True)
            
            # 문서 삭제 (소스가 일치하는 모든 문서 삭제)
            removed_count = 0
            if hasattr(vectorstore, 'docstore') and hasattr(vectorstore.docstore, '_dict'):
                # 삭제할 문서 ID 목록 수집
                docs_to_remove = []
                for doc_id, doc in vectorstore.docstore._dict.items():
                    if doc.metadata.get('source') == source:
                        docs_to_remove.append(doc_id)
                        removed_count += 1
                
                # 문서 삭제
                for doc_id in docs_to_remove:
                    del vectorstore.docstore._dict[doc_id]
                
                # 인덱스 매핑에서도 제거
                if hasattr(vectorstore, 'index_to_docstore_id'):
                    # 새로운 매핑 생성
                    new_index_mapping = {}
                    for idx, d_id in vectorstore.index_to_docstore_id.items():
                        if d_id not in docs_to_remove:
                            new_index_mapping[idx] = d_id
                    
                    # 매핑 업데이트
                    vectorstore.index_to_docstore_id = new_index_mapping
                
                # 벡터스토어 다시 저장
                vectorstore.save_local(db_id)
                
                # 메타데이터 업데이트
                metadata = load_db_metadata()
                if db_id in metadata:
                    metadata[db_id]['last_updated'] = datetime.datetime.now().isoformat()
                    save_db_metadata(metadata)
                
                return jsonify({
                    'status': 'success', 
                    'message': f'문서 출처 "{source}"에서 {removed_count}개 항목이 삭제되었습니다.',
                    'removed_count': removed_count,
                    'source': source
                })
            else:
                return jsonify({'status': 'error', 'message': '벡터 DB 문서 저장소에 접근할 수 없습니다.'}), 500
        except Exception as e:
            print(f"문서 출처 삭제 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'status': 'error', 'message': f'문서 출처 삭제 중 오류: {str(e)}'}), 500



    @app.route('/update_document_custom_name', methods=['POST'])
    def update_document_custom_name():
        data = request.json
        db_id = data.get('db_id')
        source = data.get('source')
        custom_name = data.get('custom_name', '')
        
        if not db_id or not source:
            return jsonify({'status': 'error', 'message': 'DB ID 또는 소스 경로가 누락되었습니다.'}), 400
        
        try:
            # 벡터 DB 로드
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vectorstore = FAISS.load_local(db_id, embeddings, allow_dangerous_deserialization=True)
            
            # 해당 소스의 문서 업데이트
            updated = 0
            for doc_id, doc in vectorstore.docstore._dict.items():
                if doc.metadata.get('source') == source:
                    doc.metadata['custom_name'] = custom_name
                    updated += 1
            
            # 변경사항 저장
            if updated > 0:
                vectorstore.save_local(db_id)
                return jsonify({'status': 'success', 'message': f'문서명이 업데이트되었습니다.'})
            else:
                return jsonify({'status': 'error', 'message': '해당 문서를 찾을 수 없습니다.'}), 404
                
        except Exception as e:
            print(f"문서명 업데이트 중 오류: {str(e)}")
            return jsonify({'status': 'error', 'message': f'오류: {str(e)}'}), 500
    
    return app