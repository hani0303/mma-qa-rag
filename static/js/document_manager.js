document.addEventListener('DOMContentLoaded', () => {
    // 요소 선택
    const documentUploadForm = document.getElementById('document-upload-form');
    const documentFilesInput = document.getElementById('document-files');
    const selectedFilesContainer = document.getElementById('selected-files-container');
    const selectedFilesList = document.getElementById('selected-files-list');
    const selectedFilesCount = document.getElementById('selected-files-count');
    const documentList = document.getElementById('document-list');
    const categorizedDbList = document.getElementById('categorized-db-list');
    const alertContainer = document.getElementById('alert-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    const backToChatBtn = document.getElementById('back-to-chat');
    const selectAllFilesCheckbox = document.getElementById('select-all-files');
    const createVectorDbBatchBtn = document.getElementById('create-vector-db-batch');
    const createBatchDbModal = document.getElementById('create-batch-db-modal');
    const selectedFilesCountModal = document.getElementById('selected-files-count-modal');
    const selectedFilesListModal = document.getElementById('selected-files-list-modal');
    const batchDbNameInput = document.getElementById('batch-db-name');
    const batchDbCategorySelect = document.getElementById('batch-db-category');
    const newCategoryForDbInput = document.getElementById('new-category-for-db');
    const addCategoryForDbBtn = document.getElementById('add-category-for-db-btn');
    const newCategoryInput = document.getElementById('new-category-input');
    const addCategoryBtn = document.getElementById('add-category-btn');
    const createBatchDbBtn = document.getElementById('create-batch-db-btn');
    const cancelBatchCreateDbBtn = document.getElementById('cancel-batch-create-db');
    const editCategoryModal = document.getElementById('edit-category-modal');
    const oldCategoryNameInput = document.getElementById('old-category-name');
    const newCategoryNameInput = document.getElementById('new-category-name');
    const saveCategoryNameBtn = document.getElementById('save-category-name-btn');
    const cancelEditCategoryBtn = document.getElementById('cancel-edit-category-btn');
    
    // 이벤트 리스너 초기화
    initEventListeners();
    
    // 이벤트 리스너 설정 함수
    function initEventListeners() {
        // 채팅으로 돌아가기 버튼
        if (backToChatBtn) {
            backToChatBtn.addEventListener('click', navigateToMainPage);
        }
        
        // 파일 선택 시 이벤트
        if (documentFilesInput) {
            documentFilesInput.addEventListener('change', handleFileSelection);
        }
        
        // 모든 파일 선택/해제 체크박스
        if (selectAllFilesCheckbox) {
            selectAllFilesCheckbox.addEventListener('change', handleSelectAllFiles);
        }
        
        // 문서 목록 이벤트 위임 (개별 체크박스 변경)
        if (documentList) {
            documentList.addEventListener('change', handleDocumentCheckboxChange);
            
            // 문서 삭제 버튼 클릭
            documentList.addEventListener('click', handleDocumentDelete);
        }
        
        // 문서 업로드 폼 제출
        if (documentUploadForm) {
            documentUploadForm.addEventListener('submit', handleDocumentUpload);
        }
        
        // 벡터 DB 일괄 생성 버튼
        if (createVectorDbBatchBtn) {
            createVectorDbBatchBtn.addEventListener('click', handleBatchDbCreation);
        }
        
        // 모달 닫기 버튼
        if (cancelBatchCreateDbBtn) {
            cancelBatchCreateDbBtn.addEventListener('click', () => {
                createBatchDbModal.classList.add('hidden');
            });
        }
        
        // DB 이름 입력 시 자동으로 소문자와 언더스코어로 변환
        if (batchDbNameInput) {
            batchDbNameInput.addEventListener('input', () => {
                // 특수문자 제한 없이 그대로 사용 (한글, 영문, 숫자, _, 공백 등)
            });
        }
        
        // 다중 파일로 벡터 DB 생성 버튼
        if (createBatchDbBtn) {
            createBatchDbBtn.addEventListener('click', handleCreateBatchDb);
        }
        
        // 카테고리 추가 버튼
        if (addCategoryBtn) {
            addCategoryBtn.addEventListener('click', handleAddCategory);
        }
        
        // DB 생성 모달에서 새 카테고리 추가
        if (addCategoryForDbBtn) {
            addCategoryForDbBtn.addEventListener('click', handleAddCategoryForDb);
        }
        
        // 카테고리 헤더 클릭 이벤트 (접기/펼치기)
        document.querySelectorAll('.category-header').forEach(header => {
            header.addEventListener('click', handleCategoryHeaderClick);
        });
        
        // 벡터 DB 카테고리 변경
        document.querySelectorAll('.category-select').forEach(select => {
            select.addEventListener('change', handleDbCategoryChange);
        });
        
        // 벡터 DB 삭제 (이벤트 위임)
        if (categorizedDbList) {
            categorizedDbList.addEventListener('click', handleVectorDbDelete);
        }
        
        // 벡터 DB에 문서 추가 버튼 클릭 (이벤트 위임)
        document.addEventListener('click', handleAddDocsToDb);
        
        // 문서 추가 모달 취소 버튼
        const cancelAddToDbBtn = document.getElementById('cancel-add-to-db');
        if (cancelAddToDbBtn) {
            cancelAddToDbBtn.addEventListener('click', () => {
                document.getElementById('add-to-db-modal').classList.add('hidden');
            });
        }
        
        // 문서 추가 모달의 모든 파일 선택/해제
        const selectAllFilesModal = document.getElementById('select-all-files-modal');
        if (selectAllFilesModal) {
            selectAllFilesModal.addEventListener('change', handleSelectAllFilesModal);
        }
        
        // 벡터 DB에 문서 추가 버튼
        const addToDbBtn = document.getElementById('add-to-db-btn');
        if (addToDbBtn) {
            addToDbBtn.addEventListener('click', handleAddDocsToDbSubmit);
        }
        
        // 문서 삭제 이벤트 (이벤트 위임)
        const dbDocumentsContainer = document.getElementById('db-documents-container');
        if (dbDocumentsContainer) {
            dbDocumentsContainer.addEventListener('click', handleDbDocumentDelete);
        }
        
        // 모달 닫기 버튼
        const closeManageDbDocsBtn = document.getElementById('close-manage-db-docs');
        if (closeManageDbDocsBtn) {
            closeManageDbDocsBtn.addEventListener('click', () => {
                document.getElementById('manage-db-docs-modal').classList.add('hidden');
            });
        }
        
        // 문서명 수정 이벤트
        if (dbDocumentsContainer) {
            dbDocumentsContainer.addEventListener('click', handleEditCustomName);
        }
        
        // 문서명 수정 취소 버튼
        const cancelCustomNameBtn = document.getElementById('cancel-custom-name-btn');
        if (cancelCustomNameBtn) {
            cancelCustomNameBtn.addEventListener('click', () => {
                document.getElementById('edit-custom-name-modal').classList.add('hidden');
            });
        }
        
        // 문서명 저장 버튼
        const saveCustomNameBtn = document.getElementById('save-custom-name-btn');
        if (saveCustomNameBtn) {
            saveCustomNameBtn.addEventListener('click', handleSaveCustomName);
        }
        
        // 카테고리 수정 관련 이벤트
        document.querySelectorAll('.edit-category-btn').forEach(btn => {
            btn.addEventListener('click', handleEditCategoryClick);
        });
        
        // 카테고리 삭제 관련 이벤트
        document.querySelectorAll('.delete-category-btn').forEach(btn => {
            btn.addEventListener('click', handleDeleteCategoryClick);
        });
        
        // 카테고리명 저장 버튼
        if (saveCategoryNameBtn) {
            saveCategoryNameBtn.addEventListener('click', handleSaveCategoryName);
        }
        
        // 카테고리 수정 취소 버튼
        if (cancelEditCategoryBtn) {
            cancelEditCategoryBtn.addEventListener('click', () => {
                editCategoryModal.classList.add('hidden');
            });
        }
    }
    
    // 파일 선택 처리 함수
    function handleFileSelection() {
        const files = documentFilesInput.files;
        
        if (files.length > 0) {
            selectedFilesContainer.classList.remove('hidden');
            selectedFilesCount.textContent = files.length;
            selectedFilesList.innerHTML = '';
            
            for (let i = 0; i < files.length; i++) {
                const fileItem = document.createElement('div');
                fileItem.className = 'selected-file';
                fileItem.textContent = files[i].name;
                selectedFilesList.appendChild(fileItem);
            }
        } else {
            selectedFilesContainer.classList.add('hidden');
        }
    }
    
    // 모든 파일 선택/해제 처리 함수
    function handleSelectAllFiles() {
        const checkboxes = document.querySelectorAll('.doc-checkbox');
        const isChecked = selectAllFilesCheckbox.checked;
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });
        
        updateBatchActions();
    }
    
    // 일괄 작업 버튼 활성화/비활성화 함수
    function updateBatchActions() {
        const checkedCount = document.querySelectorAll('.doc-checkbox:checked').length;
        createVectorDbBatchBtn.disabled = checkedCount === 0;
    }
    
    // 개별 체크박스 변경 처리 함수
    function handleDocumentCheckboxChange(e) {
        if (e.target.classList.contains('doc-checkbox')) {
            updateBatchActions();
            
            // 모든 체크박스가 선택되었는지 확인
            const allCheckboxes = document.querySelectorAll('.doc-checkbox');
            const checkedCount = document.querySelectorAll('.doc-checkbox:checked').length;
            
            if (allCheckboxes.length === checkedCount) {
                selectAllFilesCheckbox.checked = true;
            } else {
                selectAllFilesCheckbox.checked = false;
            }
        }
    }
    
    // 문서 삭제 처리 함수
    function handleDocumentDelete(e) {
        if (e.target.closest('.delete-document-btn')) {
            const btn = e.target.closest('.delete-document-btn');
            const storageFilename = btn.dataset.storageFilename;
            const displayName = btn.dataset.displayName;
            
            if (confirm(`정말로 "${displayName}" 파일을 삭제하시겠습니까?`)) {
                deleteDocument(storageFilename, displayName);
            }
        }
    }
    
    // 문서 삭제 AJAX 요청 함수
    async function deleteDocument(storageFilename, displayName) {
        showLoading();
        
        try {
            const response = await fetch('/delete_document', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ storage_filename: storageFilename })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showAlert(data.message, 'success');
                // 페이지 새로고침하여 문서 목록 업데이트
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('문서 삭제 중 오류가 발생했습니다.', 'danger');
        } finally {
            hideLoading();
        }
    }
    
    // 문서 업로드 처리 함수
    async function handleDocumentUpload(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const files = documentFilesInput.files;
        
        if (!files.length) {
            showAlert('파일을 선택해주세요.', 'danger');
            return;
        }
        
        // 여러 파일 추가
        for (let i = 0; i < files.length; i++) {
            formData.append('documents[]', files[i]);
        }
        
        showLoading();
        
        try {
            const response = await fetch('/upload_documents', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showAlert(data.message, 'success');
                // 페이지 새로고침하여 문서 목록 업데이트
                location.reload();
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('문서 업로드 중 오류가 발생했습니다.', 'danger');
        } finally {
            hideLoading();
            documentUploadForm.reset();
            selectedFilesContainer.classList.add('hidden');
        }
    }
    
    // 벡터 DB 일괄 생성 처리 함수
    function handleBatchDbCreation() {
        const checkedCheckboxes = document.querySelectorAll('.doc-checkbox:checked');
        if (!checkedCheckboxes.length) return;
        
        const selectedFiles = [];
        const selectedFileDisplayNames = [];
        
        checkedCheckboxes.forEach(checkbox => {
            selectedFiles.push(checkbox.dataset.storageFilename);
            // 화면에 표시되는 파일명 추출
            const displayName = checkbox.closest('.document-item').querySelector('.document-name').textContent;
            selectedFileDisplayNames.push(displayName);
        });
        
        // 모달에 선택한 파일 표시
        selectedFilesCountModal.textContent = selectedFiles.length;
        selectedFilesListModal.innerHTML = '';
        
        selectedFileDisplayNames.forEach(displayName => {
            const fileItem = document.createElement('div');
            fileItem.className = 'selected-file';
            
            // 파일 타입에 따른 아이콘 추가
            let iconClass = 'fa-file-alt';
            if (displayName.endsWith('.pdf')) iconClass = 'fa-file-pdf';
            else if (displayName.endsWith('.docx') || displayName.endsWith('.doc')) iconClass = 'fa-file-word';
            else if (displayName.endsWith('.xlsx') || displayName.endsWith('.xls')) iconClass = 'fa-file-excel';
            else if (displayName.endsWith('.pptx') || displayName.endsWith('.ppt')) iconClass = 'fa-file-powerpoint';
            else if (displayName.endsWith('.jpg') || displayName.endsWith('.jpeg') || 
                    displayName.endsWith('.png') || displayName.endsWith('.gif')) iconClass = 'fa-file-image';
            else if (displayName.endsWith('.hwp')) iconClass = 'fa-file-alt';
            
            fileItem.innerHTML = `<i class="fas ${iconClass} file-type-icon"></i> ${displayName}`;
            selectedFilesListModal.appendChild(fileItem);
        });
        
        // DB 이름 초기값 설정 (현재 날짜 + 시간 기반)
        const now = new Date();
        const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
        const timeStr = `${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
        batchDbNameInput.value = `DB_${dateStr}_${timeStr}`;
        
        // 모달 표시
        createBatchDbModal.classList.remove('hidden');
    }
    
    // 다중 파일로 벡터 DB 생성 처리 함수
    async function handleCreateBatchDb() {
        const dbName = batchDbNameInput.value.trim();
        // 문서 이름 입력값 가져오기
        const documentName = document.getElementById('batch-document-name').value.trim();
        const checkedCheckboxes = document.querySelectorAll('.doc-checkbox:checked');
        const selectedFiles = [];
        
        // 고급 설정 값 가져오기
        const chunkSizeInput = document.getElementById('chunk-size');
        const chunkOverlapInput = document.getElementById('chunk-overlap');
        
        let chunkSize = 300; // 기본값
        let chunkOverlap = 50; // 기본값
        
        // 입력 필드가 존재하면 값 가져오기
        if (chunkSizeInput) {
            chunkSize = parseInt(chunkSizeInput.value, 10) || 300;
            if (chunkSize < 100) chunkSize = 100; // 최소값 설정
        }
        
        if (chunkOverlapInput) {
            chunkOverlap = parseInt(chunkOverlapInput.value, 10) || 50;
            if (chunkOverlap < 0) chunkOverlap = 0; // 최소값 설정
            if (chunkOverlap >= chunkSize) chunkOverlap = Math.floor(chunkSize / 2); // 청크 크기보다 작게 설정
        }
        
        checkedCheckboxes.forEach(checkbox => {
            selectedFiles.push(checkbox.dataset.storageFilename);
        });
        
        if (!dbName) {
            showAlert('벡터 DB 이름을 입력해주세요.', 'danger');
            return;
        }
        
        showLoading();
        createBatchDbModal.classList.add('hidden');
        
        try {
            // 카테고리 정보 가져오기
            const categorySelect = document.getElementById('batch-db-category');
            let selectedCategory = '기타'; // 기본값
            
            if (categorySelect && categorySelect.value) {
                selectedCategory = categorySelect.value;
            } else {
                // 사용자 입력 카테고리 확인
                const newCategoryInput = document.getElementById('new-category-for-db');
                if (newCategoryInput && newCategoryInput.value.trim()) {
                    selectedCategory = newCategoryInput.value.trim();
                }
            }
            
            // 선택된 PDF 로더 가져오기
            const pdfLoaderSelect = document.getElementById('pdf-loader-select');
            const selectedPdfLoader = pdfLoaderSelect ? pdfLoaderSelect.value : 'pdfplumber';
            
            const response = await fetch('/create_vector_db_from_multiple', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    storage_filenames: selectedFiles,
                    db_name: dbName,
                    document_name: documentName, // 문서 이름 추가
                    chunk_size: chunkSize,
                    chunk_overlap: chunkOverlap,
                    category: selectedCategory,
                    pdf_loader: selectedPdfLoader
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showAlert(`${data.message} (청크 크기: ${data.chunk_size}, 오버랩: ${data.chunk_overlap})`, 'success');
                // 페이지 새로고침하여 DB 목록 업데이트
                location.reload();
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('벡터 DB 생성 중 오류가 발생했습니다: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }
    
    // 카테고리 추가 처리 함수
    async function handleAddCategory() {
        const categoryName = newCategoryInput.value.trim();
        
        if (!categoryName) {
            showAlert('카테고리 이름을 입력해주세요.', 'danger');
            return;
        }
        
        try {
            const response = await fetch('/add_category', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ category_name: categoryName })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showAlert(data.message, 'success');
                // 페이지 새로고침하여 카테고리 목록 업데이트
                location.reload();
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('카테고리 추가 중 오류가 발생했습니다.', 'danger');
        }
    }
    
    // DB 생성 모달에서 새 카테고리 추가 함수
    async function handleAddCategoryForDb() {
        const categoryName = newCategoryForDbInput.value.trim();
        
        if (!categoryName) {
            showAlert('카테고리 이름을 입력해주세요.', 'danger');
            return;
        }
        
        try {
            const response = await fetch('/add_category', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ category_name: categoryName })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // 카테고리 셀렉트 박스에 새 옵션 추가
                const option = document.createElement('option');
                option.value = categoryName;
                option.textContent = categoryName;
                option.selected = true;
                batchDbCategorySelect.appendChild(option);
                
                newCategoryForDbInput.value = '';
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('카테고리 추가 중 오류가 발생했습니다.', 'danger');
        }
    }
    
    // 카테고리 헤더 클릭 이벤트 처리 함수
    function handleCategoryHeaderClick() {
        const categoryName = this.getAttribute('data-category');
        const content = document.getElementById(`category-${categoryName.replace(' ', '-')}`);
        
        if (content) {
            content.style.display = content.style.display === 'none' ? 'block' : 'none';
            
            // 아이콘 변경
            const icon = this.querySelector('.fas');
            if (icon) {
                icon.classList.toggle('fa-chevron-down');
                icon.classList.toggle('fa-chevron-right');
            }
        }
    }
    
    // DB 카테고리 변경 처리 함수
    async function handleDbCategoryChange() {
        const dbId = this.getAttribute('data-db-id');
        const newCategory = this.value;
        
        console.log('DB ID:', dbId); // 디버깅용 로그
        console.log('New Category:', newCategory); // 디버깅용 로그
        
        try {
            const response = await fetch('/update_db_category', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ db_id: dbId, category: newCategory })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showAlert(data.message, 'success');
                // 페이지 새로고침하여 변경사항 반영
                setTimeout(() => location.reload(), 1000);
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('카테고리 변경 중 오류가 발생했습니다.', 'danger');
        }
    }
    
    // 벡터 DB 삭제 처리 함수
    function handleVectorDbDelete(e) {
        if (e.target.closest('.delete-db-btn')) {
            const btn = e.target.closest('.delete-db-btn');
            const dbId = btn.dataset.dbId;  
            const dbName = btn.dataset.dbName;
            
            if (confirm(`정말로 "${dbName}" 벡터 DB를 삭제하시겠습니까?`)) {
                deleteVectorDB(dbId);
            }
        }
    }
    
    // 벡터 DB 삭제 AJAX 요청 함수
    async function deleteVectorDB(dbId) {
        showLoading();
        
        try {
            const response = await fetch('/delete_vector_db', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ db_id: dbId })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showAlert(data.message, 'success');
                // 페이지 새로고침하여 DB 목록 업데이트
                location.reload();
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('벡터 DB 삭제 중 오류가 발생했습니다.', 'danger');
        } finally {
            hideLoading();
        }
    }
    
    // 벡터 DB에 문서 추가 버튼 클릭 처리 함수
    function handleAddDocsToDb(e) {
        if (e.target.closest('.add-docs-btn')) {
            const btn = e.target.closest('.add-docs-btn');
            const dbId = btn.dataset.dbId;
            const dbName = btn.dataset.dbName;
            
            // 타겟 DB 정보 설정
            document.getElementById('target-db-id').value = dbId;
            document.getElementById('target-db-name').textContent = dbName;
            
            // 파일 목록 로드
            loadFilesForDb();
            
            // 모달 표시
            document.getElementById('add-to-db-modal').classList.remove('hidden');
        }
    }
    
    // 모달에서 모든 파일 선택/해제 처리 함수
    function handleSelectAllFilesModal() {
        const checkboxes = document.querySelectorAll('#add-files-list .file-checkbox');
        const isChecked = document.getElementById('select-all-files-modal').checked;
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });
    }
    
    // 파일 목록 로드 함수
    function loadFilesForDb() {
        // 파일 목록 비우기
        const addFilesList = document.getElementById('add-files-list');
        if (!addFilesList) return;
        
        addFilesList.innerHTML = '';
        
        // 문서 목록에서 파일 가져오기
        const documents = document.querySelectorAll('.document-item');
        
        if (documents.length === 0) {
            addFilesList.innerHTML = '<p>업로드된 문서가 없습니다. 먼저 문서를 업로드해주세요.</p>';
            return;
        }
        
        // 각 파일을 목록에 추가
        documents.forEach(doc => {
            const fileName = doc.querySelector('.document-name').textContent;
            const storageFileName = doc.querySelector('.doc-checkbox').dataset.storageFilename;
            
            const fileItem = document.createElement('div');
            fileItem.className = 'file-list-item';
            
            // 파일 타입에 따른 아이콘 추가
            let iconClass = 'fa-file-alt';
            if (fileName.endsWith('.pdf')) iconClass = 'fa-file-pdf';
            else if (fileName.endsWith('.docx') || fileName.endsWith('.doc')) iconClass = 'fa-file-word';
            else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) iconClass = 'fa-file-excel';
            else if (fileName.endsWith('.pptx') || fileName.endsWith('.ppt')) iconClass = 'fa-file-powerpoint';
            else if (fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') || 
                    fileName.endsWith('.png') || fileName.endsWith('.gif')) iconClass = 'fa-file-image';
            else if (fileName.endsWith('.hwp')) iconClass = 'fa-file-alt';
            
            fileItem.innerHTML = `
                <div class="file-item-content">
                    <input type="checkbox" class="file-checkbox" data-storage-filename="${storageFileName}">
                    <span><i class="fas ${iconClass} file-type-icon"></i> ${fileName}</span>
                </div>
                <div class="custom-name-field">
                    <label for="custom-name-${storageFileName}">사용자 지정 문서명:</label>
                    <input type="text" id="custom-name-${storageFileName}" class="custom-name-input" 
                        data-storage-filename="${storageFileName}" placeholder="기본값: 원본 파일명" value="${fileName}">
                </div>
            `;
            
            addFilesList.appendChild(fileItem);
        });
    }
    
    // 벡터 DB에 문서 추가 제출 처리 함수
    async function handleAddDocsToDbSubmit() {
        const dbId = document.getElementById('target-db-id').value;
        const checkboxes = document.querySelectorAll('#add-files-list .file-checkbox:checked');
        
        if (!checkboxes.length) {
            showAlert('추가할 문서를 선택해주세요.', 'danger');
            return;
        }
        
        const selectedFiles = [];
        const customNames = {}; // 사용자 지정 문서명 저장
        
        checkboxes.forEach(checkbox => {
            const storageFilename = checkbox.dataset.storageFilename;
            selectedFiles.push(storageFilename);
            
            // 사용자 지정 문서명 가져오기
            const customNameInput = document.getElementById(`custom-name-${storageFilename}`);
            if (customNameInput && customNameInput.value.trim()) {
                customNames[storageFilename] = customNameInput.value.trim();
            }
        });
        
        console.log('선택된 파일:', selectedFiles); // 디버깅용 로그
        console.log('사용자 지정 문서명:', customNames); // 디버깅용 로그
        console.log('대상 DB ID:', dbId); // 디버깅용 로그
        
        showLoading();
        
        try {
            const response = await fetch('/add_documents_to_db', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    db_id: dbId,
                    storage_filenames: selectedFiles,
                    custom_names: customNames // 사용자 지정 문서명 전송
                })
            });
            
            if (!response.ok) {
                throw new Error(`서버 응답 오류: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showAlert(data.message, 'success');
                
                // 성공 후 모달 닫기
                document.getElementById('add-to-db-modal').classList.add('hidden');
            } else {
                showAlert(data.message || '알 수 없는 오류가 발생했습니다.', 'danger');
            }
        } catch (error) {
            console.error('요청 오류:', error);
            showAlert('문서 추가 중 오류가 발생했습니다: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }
    
    // 벡터 DB 문서 관리 버튼 클릭 이벤트 처리
    document.addEventListener('click', (e) => {
        if (e.target.closest('.manage-docs-btn')) {
            const btn = e.target.closest('.manage-docs-btn');
            const dbId = btn.dataset.dbId;
            const dbName = btn.dataset.dbName;
            
            console.log('문서 관리 버튼 클릭됨');
            console.log('DB ID:', dbId);
            console.log('DB Name:', dbName);
            
            // 타겟 DB 정보 설정
            document.getElementById('manage-db-id').value = dbId;
            document.getElementById('manage-db-name').textContent = dbName;
            
            // 문서 목록 로드
            loadDbDocuments(dbId);
            
            // 모달 표시
            document.getElementById('manage-db-docs-modal').classList.remove('hidden');
        }
    });
    
    // 벡터 DB 문서 목록 로드 함수
    async function loadDbDocuments(dbId) {
        // 로딩 메시지 표시
        const dbDocumentsContainer = document.getElementById('db-documents-container');
        if (!dbDocumentsContainer) return;
        
        dbDocumentsContainer.innerHTML = '<div class="loading-message">문서 정보를 불러오는 중...</div>';
        
        try {
            const response = await fetch('/get_db_documents', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ db_id: dbId })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // 문서 카운트 업데이트
                document.getElementById('document-count').textContent = data.count;
                
                // 문서 정보 표시
                dbDocumentsContainer.innerHTML = '<div class="document-info-section">이 벡터 DB에는 총 ' + data.count + '개의 문서 조각이 있습니다. 아래는 소스별 문서 목록입니다.</div>';
                
                // 원본 문서 소스별로 그룹화하여 표시
                const documentsBySource = {};
                
                // 그룹화
                data.documents.forEach(doc => {
                    const source = doc.source || '알 수 없는 출처';
                    if (!documentsBySource[source]) {
                        documentsBySource[source] = {
                            docs: [],
                            filename: doc.original_filename || doc.filename || source.split('/').pop() || '알 수 없는 파일'
                        };
                    }
                    documentsBySource[source].docs.push(doc);
                });
                
                // 소스 목록 생성
                const sourceList = document.createElement('div');
                sourceList.className = 'source-list-section';
                
                Object.keys(documentsBySource).sort().forEach(source => {
                    const sourceInfo = documentsBySource[source];
                    const docsCount = sourceInfo.docs.length;
                    const displayFileName = sourceInfo.filename;
                    
                    // 소스 아이템 생성
                    // 메타데이터 정보 가져오기
                    const firstDoc = sourceInfo.docs[0];
                    const customName = firstDoc.custom_name || displayFileName;
                    const metadataKeys = firstDoc.metadata ? Object.keys(firstDoc.metadata) : [];
                    let metadataHtml = '';

                    if (metadataKeys.length > 0) {
                        metadataHtml = '<div class="metadata-info">';
                        metadataKeys.forEach(key => {
                            if (key !== 'source' && key !== 'original_filename') {
                                metadataHtml += `<span class="metadata-item"><strong>${key}:</strong> ${firstDoc.metadata[key]}</span>`;
                            }
                        });
                        metadataHtml += '</div>';
                    }

                    // 소스 아이템 생성
                    const sourceItem = document.createElement('div');
                    sourceItem.className = 'source-item';
                    sourceItem.innerHTML = `
                        <div class="source-name" title="${source}">
                            <i class="fas fa-file-alt"></i> ${displayFileName}
                        </div>
                        <div class="custom-name-container">
                            <span class="custom-name-label">문서명:</span>
                            <span class="custom-name-display">${sourceInfo.docs[0].metadata?.custom_name || displayFileName}</span>
                            <button class="btn btn-small edit-custom-name-btn" data-source="${source}" data-db-id="${dbId}">
                                <i class="fas fa-edit"></i>
                            </button>
                        </div>
                        <div class="source-info">${docsCount}개 조각</div>
                        <div class="source-actions">
                            <button class="btn btn-small delete-source-btn" data-source="${source}">
                                <i class="fas fa-trash"></i> 문서 삭제
                            </button>
                        </div>
                    `;
                    
                    sourceList.appendChild(sourceItem);
                });
                
                dbDocumentsContainer.appendChild(sourceList);
                
                if (Object.keys(documentsBySource).length === 0) {
                    dbDocumentsContainer.innerHTML = '<div class="empty-message">문서가 없습니다.</div>';
                }
            } else {
                dbDocumentsContainer.innerHTML = `<div class="error-message">문서 정보 로드 실패: ${data.message}</div>`;
            }
        } catch (error) {
            console.error('문서 정보 로드 중 오류:', error);
            dbDocumentsContainer.innerHTML = `<div class="error-message">문서 정보 로드 중 오류: ${error.message}</div>`;
        }
    }
    
    // 출처별 문서 전체 삭제 이벤트 처리 함수
    async function handleDbDocumentDelete(e) {
        const deleteSourceBtn = e.target.closest('.delete-source-btn');
        if (deleteSourceBtn) {
            const source = deleteSourceBtn.getAttribute('data-source');
            const dbId = document.getElementById('manage-db-id').value;
            
            console.log('삭제 버튼 클릭됨');
            console.log('소스:', source);
            console.log('DB ID:', dbId);
            
            if (confirm(`정말로 이 문서를 벡터 DB에서 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.`)) {
                showLoading();
                
                try {
                    const response = await fetch('/remove_documents_by_source', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            db_id: dbId,
                            source: source
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`서버 응답 오류: ${response.status} ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        showAlert(data.message, 'success');
                        
                        // 문서 목록 다시 로드
                        loadDbDocuments(dbId);
                    } else {
                        showAlert(data.message || '알 수 없는 오류가 발생했습니다.', 'danger');
                    }
                } catch (error) {
                    console.error('문서 출처 삭제 중 오류:', error);
                    showAlert(`문서 출처 삭제 중 오류: ${error.message}`, 'danger');
                } finally {
                    hideLoading();
                }
            }
        }
    }
    
    // 문서명 수정 이벤트 처리 함수
    function handleEditCustomName(e) {
        const editBtn = e.target.closest('.edit-custom-name-btn');
        if (editBtn) {
            const source = editBtn.getAttribute('data-source');
            const dbId = editBtn.getAttribute('data-db-id');
            const customName = editBtn.closest('.source-item').querySelector('.custom-name-display').textContent;
            
            // 모달 필드 설정
            document.getElementById('edit-source-path').value = source;
            document.getElementById('edit-db-id').value = dbId;
            document.getElementById('custom-name-input').value = customName;
            
            // 모달 표시
            document.getElementById('edit-custom-name-modal').classList.remove('hidden');
        }
    }
    
    // 문서명 저장 버튼 처리 함수
    async function handleSaveCustomName() {
        const sourcePath = document.getElementById('edit-source-path').value;
        const dbId = document.getElementById('edit-db-id').value;
        const newCustomName = document.getElementById('custom-name-input').value.trim();
        
        showLoading();
        
        try {
            const response = await fetch('/update_document_custom_name', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    db_id: dbId,
                    source: sourcePath,
                    custom_name: newCustomName
                })
            });
            
            const data = await response.json();
            
            // 로딩 숨김 (에러가 발생해도 항상 숨겨야 함)
            hideLoading();
            
            if (data.status === 'success') {
                // 모달 직접 참조하여 강제로 숨김 처리
                const modal = document.getElementById('edit-custom-name-modal');
                if (modal) {
                    modal.classList.add('hidden');
                    console.log('모달 숨김 처리됨');
                }
                
                // 성공 메시지 표시
                showAlert(data.message, 'success');
                
                // 문서 목록 다시 로드
                loadDbDocuments(dbId);
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('문서명 업데이트 중 오류가 발생했습니다.', 'danger');
            // 로딩 숨김 (에러가 발생해도 항상 숨겨야 함)
            hideLoading();
        }
    }
    
    // 카테고리 편집 버튼 클릭 처리 함수
    function handleEditCategoryClick() {
        const category = this.getAttribute('data-category');
        
        // 모달 필드 설정
        oldCategoryNameInput.value = category;
        newCategoryNameInput.value = category;
        
        // 모달 표시
        editCategoryModal.classList.remove('hidden');
    }
    
    // 카테고리 삭제 버튼 클릭 처리 함수
    function handleDeleteCategoryClick() {
        const category = this.getAttribute('data-category');
        
        if (confirm(`정말로 "${category}" 카테고리를 삭제하시겠습니까?`)) {
            deleteCategory(category);
        }
    }
    
    // 카테고리 삭제 AJAX 요청 함수
    async function deleteCategory(category) {
        showLoading();
        
        try {
            const response = await fetch('/delete_category', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ category_name: category })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showAlert(data.message, 'success');
                // 페이지 새로고침하여 카테고리 목록 업데이트
                location.reload();
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('카테고리 삭제 중 오류가 발생했습니다.', 'danger');
        } finally {
            hideLoading();
        }
    }
    
    // 카테고리명 저장 처리 함수
    async function handleSaveCategoryName() {
        const oldName = oldCategoryNameInput.value;
        const newName = newCategoryNameInput.value.trim();
        
        if (!newName) {
            showAlert('새 카테고리 이름을 입력해주세요.', 'danger');
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch('/update_category', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    old_category: oldName,
                    new_category: newName
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showAlert(data.message, 'success');
                // 모달 닫기
                editCategoryModal.classList.add('hidden');
                // 페이지 새로고침하여 카테고리 목록 업데이트
                location.reload();
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('카테고리 이름 변경 중 오류가 발생했습니다.', 'danger');
        } finally {
            hideLoading();
        }
    }
});