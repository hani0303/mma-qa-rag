document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM이 로드되었습니다');
    
    // 요소 선택
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const clearBtn = document.getElementById('clear-btn');
    const statusContainer = document.getElementById('status-container');
    const statusText = document.getElementById('status-text');
    const statusSteps = document.getElementById('status-steps');
    const feedbackModal = document.getElementById('feedback-modal');
    const submitFeedbackBtn = document.getElementById('submit-feedback');
    const cancelFeedbackBtn = document.getElementById('cancel-feedback');
    // 라디오 버튼 이벤트 리스너 추가
    const dbRadioButtons = document.querySelectorAll('input[name="db-selector"]');
    
    // DB 전환 상태 추적 변수
    let isChangingDB = false;
    // DB 전환 지연시간 (밀리초) - 사전 로드로 매우 짧게 설정
    const dbSwitchDelay = 200; // 거의 즉시 전환되게 설정
    // 메시지 전환 표시 시간 (밀리초) - 너무 빠르면 사용자가 변화를 인지하지 못할 수 있음
    const messageDisplayDelay = 300;
    // DB 전환 시간 측정 (디버깅용)
    let dbSwitchStartTime = 0;
    // EventSource 변수 선언
    let eventSource = null;

    // 초기 메시지 로드
    loadInitialMessages();
    
    // 이벤트 리스너
    if (userInput) {
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                console.log('Enter 키가 눌렸습니다');
                sendMessage();
            }
        });
    } else {
        console.error('user-input 요소를 찾을 수 없습니다');
    }
    
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            console.log('Send 버튼이 클릭되었습니다');
            sendMessage();
        });
    } else {
        console.error('send-btn 요소를 찾을 수 없습니다');
    }
    
    if (clearBtn) {
        clearBtn.addEventListener('click', clearConversation);
    } else {
        console.error('clear-btn 요소를 찾을 수 없습니다');
    }
    
    if (submitFeedbackBtn) {
        submitFeedbackBtn.addEventListener('click', submitFeedback);
    }
    
    if (cancelFeedbackBtn) {
        cancelFeedbackBtn.addEventListener('click', () => {
            feedbackModal.classList.add('hidden');
        });
    }
    
    // 카테고리 폴더 클릭 이벤트 처리
    initCategoryFolders();

    // 자동 DB 선택 함수 추가
    function autoSelectFirstDB() {
        const dbRadioButtons = document.querySelectorAll('input[name="db-selector"]');
        if (dbRadioButtons.length > 0 && !document.querySelector('input[name="db-selector"]:checked')) {
            // 첫 번째 DB 선택
            dbRadioButtons[0].checked = true;
            
            // DB 변경 API 호출
            changeDB(dbRadioButtons[0].value, dbRadioButtons[0].nextElementSibling.textContent.trim());
        }
    }

    // DB 변경 함수
    async function changeDB(dbId, dbName) {
        if (isChangingDB) return;
        
        isChangingDB = true;
        dbSwitchStartTime = performance.now();
        
        try {
            const response = await fetch('/change_db', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ db_index: dbId })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                console.log(`DB가 '${dbName}'으로 자동 선택되었습니다`);
                
                // 첫 DB 자동 선택 시 채팅창 초기화는 하지 않음
                isChangingDB = false;
            } else {
                throw new Error(data.message || 'DB 변경 중 오류가 발생했습니다.');
            }
        } catch (error) {
            console.error('DB 변경 오류:', error);
            isChangingDB = false;
        }
    }

    // 페이지 로드 시 자동 DB 선택 실행
    autoSelectFirstDB();
    
    // 문서 관리 페이지로 이동
    const adminLockIcon = document.getElementById('admin-lock-icon');
    if (adminLockIcon) {
        adminLockIcon.addEventListener('click', navigateToDocumentManager);
    } else {
        console.error('admin-lock-icon 요소를 찾을 수 없습니다');
    }
    
    // 카테고리 폴더 초기화 함수
    // 카테고리 폴더 초기화 함수
    function initCategoryFolders() {
        const categoryHeaders = document.querySelectorAll('.category-header');
        
        // 모든 카테고리 항목을 기본적으로 표시
        document.querySelectorAll('.category-items').forEach(container => {
            container.style.display = 'block';
        });
        
        // 모든 폴더 아이콘을 열린 상태로 변경
        document.querySelectorAll('.category-header .fas').forEach(icon => {
            icon.classList.remove('fa-folder-closed');
            icon.classList.add('fa-folder-open');
        });
        
        categoryHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const categoryName = header.getAttribute('data-category');
                const itemsContainer = document.getElementById(`category-items-${categoryName.replace(' ', '-')}`);
                const folderIcon = header.querySelector('.fas');
                
                if (itemsContainer) {
                    // 표시 상태 토글
                    const isHidden = itemsContainer.style.display === 'none';
                    itemsContainer.style.display = isHidden ? 'block' : 'none';
                    
                    // 아이콘 변경
                    if (folderIcon) {
                        folderIcon.classList.toggle('fa-folder-closed');
                        folderIcon.classList.toggle('fa-folder-open');
                    }
                    
                    // 다른 카테고리는 닫기
                    if (isHidden) {
                        document.querySelectorAll('.category-items').forEach(container => {
                            if (container !== itemsContainer) {
                                container.style.display = 'none';
                                const otherHeader = container.previousElementSibling;
                                if (otherHeader) {
                                    const icon = otherHeader.querySelector('.fas');
                                    if (icon) {
                                        icon.classList.remove('fa-folder-open');
                                        icon.classList.add('fa-folder-closed');
                                    }
                                }
                            }
                        });
                    }
                }
            });
        });
        
        // 초기 상태에서 선택된 DB가 있는 카테고리 자동 펼침 (이미 모두 펼쳐져 있으므로 여기서는 필요 없음)
    }
    
    // 메시지 전송 함수
    async function sendMessage() {
        // DB 전환 중이면 무시
        if (isChangingDB) {
            addErrorMessage('현재 벡터 DB를 전환 중입니다. 잠시 후 다시 시도해주세요.');
            return;
        }

        console.log('sendMessage 함수가 호출되었습니다');
        const message = userInput.value.trim();
        
        if (!message) {
            console.log('메시지가 비어있습니다');
            return;
        }
        
        // DB 선택 여부 확인
        const selectedDb = document.querySelector('input[name="db-selector"]:checked');
        if (!selectedDb) {
            // DB가 선택되지 않았으면 자동으로 첫 번째 DB 선택
            autoSelectFirstDB();
            // 약간의 지연 후 메시지 전송 재시도
            setTimeout(sendMessage, 500);
            return;
        }
        
        console.log('보내는 메시지:', message);
        
        // 사용자 메시지 추가
        addMessageToChat('user', message);
        userInput.value = '';
        
        // 처리 단계 스트리밍 시작
        const threadId = startProgressStream();
        
        try {
            console.log('서버에 요청을 보냅니다');
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    question: message, 
                    thread_id: threadId 
                })
            });
            
            console.log('서버 응답:', response);
            
            if (!response.ok) {
                const errorData = await response.json();
                if (errorData.status === 'no_db_selected') {
                    throw new Error('벡터 DB를 선택해주세요. 좌측 사이드바에서 DB를 선택한 후 질문해주세요.');
                } else {
                    throw new Error(`HTTP 오류! 상태: ${response.status}`);
                }
            }
            
            const data = await response.json();
            console.log('받은 데이터:', data);
            
            if (data.status === 'success') {
                // AI 응답 추가 (URL 자동 링크 기능 추가)
                addMessageToChat('assistant', data.answer);
                
                // 피드백 버튼 추가
                addFeedbackButton();
            } else {
                throw new Error(data.error || '응답 처리 중 오류가 발생했습니다.');
            }
        } catch (error) {
            console.error('오류 발생:', error);
            addErrorMessage(error.message);
        } finally {
            // 진행 상태 스트림 종료
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
            
            // 약간의 지연 후 상태 컨테이너 숨김 (모든 메시지 표시 보장)
            setTimeout(() => {
                if (statusContainer) {
                    statusContainer.classList.add('hidden');
                }
            }, 500);
        }
    }

    
        
    // 채팅에 메시지 추가 함수
    // 채팅에 메시지 추가 함수
    function addMessageToChat(role, content) {
        console.log(`메시지 추가: role=${role}, 내용 일부=${content.substring(0, 30)}...`);
        
        if (!chatContainer) {
            console.error('chat-container를 찾을 수 없습니다');
            return;
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role === 'user' ? 'user-message' : 'bot-message'}`;
        
        const avatar = document.createElement('span');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? '🙎‍♂️' : '😊';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // URL을 자동으로 링크로 변환
        if (role === 'assistant') {
            // 메시지에 파이프(|) 형식의 데이터가 있는지 확인
            const pipeSeparatedLines = content.match(/^(.+?)\s*\|\s*(.+?)\s*(\|.+)?$/gm);
            
            if (pipeSeparatedLines && pipeSeparatedLines.length > 1) {
                // 파이프 형식 데이터가 있으면 테이블로 변환
                const tableHtml = convertPipeTextToTable(content);
                messageContent.innerHTML = tableHtml;
            } else {
                // 아스트리스크 2개로 감싸진 텍스트를 이모티콘으로 대체
                let processedContent = content
                    .replace(/\n/g, '<br>') // 줄바꿈 처리
                    .replace(/\*\*Source\*\*\s*-/, '<br>**Source**<br>-') // Source 다음에 줄바꿈 추가
                    .replace(/\*\*([^*]+)\*\*/g, function(match, p1) {
                        // 아스트리스크 2개로 감싸진 텍스트에 따라 적절한 이모티콘 선택
                        if (p1.includes('날짜')) return '📅 ' + p1;
                        if (p1.includes('장소')) return '📍 ' + p1;
                        if (p1.includes('내용')) return '📝 ' + p1;
                        if (p1.includes('원인')) return '🔍 ' + p1;
                        if (p1.includes('사고')) return '⚠️ ' + p1;
                        if (p1.toLowerCase().includes('ops')) return '📋 ' + p1;
                        if (p1.includes('도장작업')) return '🏗️ ' + p1;
                        if (p1.includes('이동식')) return '🚜 ' + p1;
                        if (p1.includes('고소작업')) return '🔧 ' + p1;
                        if (p1.includes('안전대')) return '🔒 ' + p1;
                        if (p1.includes('체크리스트')) return '✅ ' + p1;
                        if (p1.includes('호')) return '🔢 ' + p1;
                        // 그 외 일반적인 경우
                        return '• ' + p1;
                    });

                // URL 패턴을 정규식으로 찾기
                const urlRegex = /(https?:\/\/[^\s]+|www\.[^\s]+)/g;
                
                // URL을 HTML 링크로 변환하고 대시(-) 앞에 줄바꿈 추가
                const linkedContent = processedContent.replace(urlRegex, function(url) {
                    // www.로 시작하는 URL에 http:// 추가
                    const fullUrl = url.startsWith('www.') ? 'http://' + url : url;
                    return `<a href="${fullUrl}" target="_blank" rel="noopener noreferrer">${url}</a>`;
                }).replace(/\s-\s/g, '<br>- '); // 대시 앞에 줄바꿈 추가
                
                messageContent.innerHTML = linkedContent;
            }
        } else {
            // 사용자 메시지는 일반 텍스트로 처리
            messageContent.textContent = content;
        }
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(avatar);
        
        chatContainer.appendChild(messageDiv);
        
        // 스크롤을 맨 아래로 이동
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // 파이프(|) 형식의 텍스트를 HTML 테이블로 변환하는 함수
    // index.js 파일의 convertPipeTextToTable 함수 내부에 다음 코드를 수정하세요:

    function convertPipeTextToTable(text) {
        // 텍스트를 줄바꿈으로 분리
        const lines = text.split('\n');
        let tableHtml = '';
        let inTable = false;
        let tableLines = [];
        
        // Source 부분을 위한 변수
        let sourceContent = '';
        let foundSource = false;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            // 점선만 있는 행 스킵 (추가된 부분)
            if (/^[-]{5,}$/.test(line) || /^[.]{5,}$/.test(line)) {
                continue;
            }
            
            // Source 부분을 찾으면 따로 저장
            if (line.includes('**Source**') || foundSource) {
                foundSource = true;
                sourceContent += line + '<br>';
                continue;
            }
            
            // 파이프(|)가 있는 행인지 확인
            if (line.includes('|')) {
                if (!inTable) {
                    inTable = true;
                }
                tableLines.push(line);
            } else if (inTable) {
                // 테이블이 끝났을 때
                tableHtml += createTableFromLines(tableLines);
                tableLines = [];
                inTable = false;
                
                // 테이블이 아닌 내용 추가
                if (line && !/^[-]{5,}$/.test(line) && !/^[.]{5,}$/.test(line)) {
                    tableHtml += `<p>${line}</p>`;
                }
            } else {
                // 일반 텍스트 행
                if (line && !/^[-]{5,}$/.test(line) && !/^[.]{5,}$/.test(line)) {
                    tableHtml += `<p>${line}</p>`;
                }
            }
        }
        
        // 아직 처리되지 않은 테이블 라인이 있으면 테이블 생성
        if (tableLines.length > 0) {
            tableHtml += createTableFromLines(tableLines);
        }
        
        // Source 내용 추가
        if (sourceContent) {
            tableHtml += `<div class="source-section">${sourceContent}</div>`;
        }
        
        return tableHtml;
    }

    // 파이프 라인 배열을 HTML 테이블로 변환
    // createTableFromLines 함수 내부 수정

    function createTableFromLines(lines) {
        // 계층적 구조 파악을 위한 정규식
        const sectionNumberRegex = /^(\d+(\.\d+)*)\s+/;
        
        let tableHtml = '<table class="result-table">';
        let isHeader = true;
        
        lines.forEach((line, index) => {
            // 점선만 있는 행 스킵 (추가된 부분)
            if (/^[-]{5,}$/.test(line.trim()) || /^[.]{5,}$/.test(line.trim())) {
                return; // 점선은 건너뛴다
            }
            
            // 앞뒤 공백 및 첫/마지막 파이프 제거
            line = line.trim().replace(/^\||\|$/g, '');
            
            // 셀 배열 생성
            const cells = line.split('|').map(cell => cell.trim());
            
            if (index === 0 && cells.length === 1) {
                // 단일 셀 헤더인 경우 컬럼 스팬 처리
                tableHtml += `<thead><tr><th colspan="2">${cells[0]}</th></tr></thead><tbody>`;
                isHeader = false;
            } else if (isHeader) {
                // 헤더 행
                tableHtml += '<thead><tr>';
                cells.forEach(cell => {
                    // 점선은 제외 (추가된 부분)
                    if (!/^[-]{5,}$/.test(cell) && !/^[.]{5,}$/.test(cell)) {
                        tableHtml += `<th>${cell}</th>`;
                    }
                });
                tableHtml += '</tr></thead><tbody>';
                isHeader = false;
            } else {
                // 일반 행 (계층 구조 확인)
                let hierarchyLevel = 0;
                let sectionNumber = '';
                
                // 첫 번째 셀에서 섹션 번호 확인하여 계층 결정
                const match = cells[0].match(sectionNumberRegex);
                if (match) {
                    sectionNumber = match[1];
                    hierarchyLevel = (match[1].match(/\./g) || []).length;
                    
                    // 섹션 번호와 내용 분리
                    cells[0] = cells[0].replace(sectionNumberRegex, '');
                    cells[0] = `<span class="section-number">${sectionNumber}</span>${cells[0]}`;
                }
                
                tableHtml += `<tr class="hierarchy-${hierarchyLevel}">`;
                cells.forEach((cell, cellIndex) => {
                    // 점선은 제외 (추가된 부분)
                    if (!/^[-]{5,}$/.test(cell) && !/^[.]{5,}$/.test(cell)) {
                        tableHtml += `<td>${cell}</td>`;
                    }
                });
                tableHtml += '</tr>';
            }
        });
        
        tableHtml += '</tbody></table>';
        return tableHtml;
    }
    
    // 에러 메시지 추가 함수
    function addErrorMessage(errorText) {
        console.log('오류 메시지 추가:', errorText);
        
        if (!chatContainer) {
            console.error('chat-container를 찾을 수 없습니다');
            return;
        }
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'chat-message bot-message error-message';
        errorDiv.textContent = `오류가 발생했습니다: ${errorText}`;
        chatContainer.appendChild(errorDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // 피드백 버튼 추가 함수
    function addFeedbackButton() {
        console.log('피드백 버튼 추가');
        
        if (!chatContainer) {
            console.error('chat-container를 찾을 수 없습니다');
            return;
        }
        
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback-request';
        
        const feedbackBtn = document.createElement('button');
        feedbackBtn.className = 'btn';
        feedbackBtn.textContent = '답변 평가하기';
        feedbackBtn.addEventListener('click', () => {
            if (feedbackModal) {
                feedbackModal.classList.remove('hidden');
            }
        });
        
        feedbackDiv.appendChild(feedbackBtn);
        chatContainer.appendChild(feedbackDiv);
    }
    
    // 피드백 제출 함수
    async function submitFeedback() {
        console.log('피드백 제출 시도');
        
        try {
            const correctnessEl = document.querySelector('input[name="correctness"]:checked');
            const helpfulnessEl = document.querySelector('input[name="helpfulness"]:checked');
            const specificityEl = document.querySelector('input[name="specificity"]:checked');
            const commentEl = document.getElementById('comment');
            
            if (!correctnessEl || !helpfulnessEl || !specificityEl) {
                console.error('평가 요소를 찾을 수 없습니다');
                return;
            }
            
            const correctness = correctnessEl.value;
            const helpfulness = helpfulnessEl.value;
            const specificity = specificityEl.value;
            const comment = commentEl ? commentEl.value : '';
            
            console.log('제출할 피드백:', { correctness, helpfulness, specificity, comment });
            
            const response = await fetch('/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    correctness: parseInt(correctness),
                    helpfulness: parseInt(helpfulness),
                    specificity: parseInt(specificity),
                    comment
                })
            });
            
            const data = await response.json();
            console.log('피드백 응답:', data);
            
            if (data.status === 'success') {
                alert('평가가 성공적으로 제출되었습니다.');
                if (feedbackModal) {
                    feedbackModal.classList.add('hidden');
                }
            } else {
                throw new Error(data.message || '평가 제출 중 오류가 발생했습니다.');
            }
        } catch (error) {
            console.error('피드백 제출 오류:', error);
            alert(`평가 제출 중 오류가 발생했습니다: ${error.message}`);
        }
    }
    
    // 대화 초기화 함수
    async function clearConversation() {
        console.log('대화 초기화 시도');
        
        try {
            const response = await fetch('/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            console.log('초기화 응답:', data);
            
            if (data.status === 'success') {
                if (chatContainer) {
                    chatContainer.innerHTML = '';
                }
                if (feedbackModal) {
                    feedbackModal.classList.add('hidden');
                }
            } else {
                throw new Error('대화 초기화 중 오류가 발생했습니다.');
            }
        } catch (error) {
            console.error('대화 초기화 오류:', error);
            alert(`대화 초기화 중 오류가 발생했습니다: ${error.message}`);
        }
    }
    
    // 초기 메시지 로드 함수
    function loadInitialMessages() {
        console.log('초기 메시지 로드');
        // 여기서는 서버 측에서 렌더링 시 제공된 메시지를 사용할 수도 있습니다
        // 예시를 위해 간단히 반복문으로 구현
        const initialMessages = []; // 서버에서 제공하는 초기 메시지
        
        initialMessages.forEach(message => {
            addMessageToChat(message.role, message.content);
        });
    }
    
    // 시스템 메시지 추가 함수
    function addSystemMessage(message) {
        console.log('시스템 메시지 추가:', message);
        
        if (!chatContainer) {
            console.error('chat-container를 찾을 수 없습니다');
            return;
        }
        
        const systemDiv = document.createElement('div');
        systemDiv.className = 'chat-message system-message';
        systemDiv.textContent = message;
        chatContainer.appendChild(systemDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // 진행 상태 스트리밍 시작 함수
    function startProgressStream() {
        if (eventSource) {
            eventSource.close();
        }
        
        // 상태 컨테이너 초기화 및 표시
        if (statusContainer) {
            statusContainer.classList.remove('hidden');
            if (statusSteps) {
                statusSteps.innerHTML = '';
            }
        }
        
        // 현재 시각을 thread_id로 사용 (중복 방지)
        const threadId = Date.now().toString();
        
        // SSE 연결 설정
        eventSource = new EventSource(`/stream_progress?thread_id=${threadId}`);
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.done) {
                // 모든 처리 단계가 완료되면 연결 종료
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                return;
            }
            
            if (data.step && statusSteps) {
                // 처리 단계 메시지 추가
                const stepElement = document.createElement('p');
                stepElement.textContent = data.step;
                statusSteps.appendChild(stepElement);
                
                // 스크롤을 가장 아래로 내림
                statusSteps.scrollTop = statusSteps.scrollHeight;
            }
        };
        
        eventSource.onerror = function() {
            console.error('SSE 연결 오류');
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
        };
        
        return threadId;
    }
    
    // 라디오 버튼 이벤트 리스너 추가 - DB 전환
    if (dbRadioButtons.length > 0) {
        dbRadioButtons.forEach(radio => {
            radio.addEventListener('change', async function() {
                if (this.checked) {
                    const selectedDB = this.value;
                    const selectedDBName = this.nextElementSibling.textContent.trim();
                    
                    // 이미 DB 전환 중이면 무시
                    if (isChangingDB) return;
    
                    // DB 전환 상태 설정
                    isChangingDB = true;
                    dbSwitchStartTime = performance.now();
                    
                    // UI 비활성화
                    userInput.disabled = true;
                    sendBtn.disabled = true;
                    
                    // 로딩 표시 (최소한의 시각적 피드백)
                    addSystemMessage(`벡터 DB를 '${selectedDBName}'로 전환 중입니다...`);
                    
                    try {
                        const response = await fetch('/change_db', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ db_index: selectedDB })
                        });
                        
                        const data = await response.json();
                        
                        if (data.status === 'success') {
                            // 채팅 창 초기화
                            if (chatContainer) {
                                chatContainer.innerHTML = '';
                            }
                            
                            // 실제 전환 시간 계산
                            const actualTime = performance.now() - dbSwitchStartTime;
                            console.log(`실제 DB 전환 시간: ${actualTime.toFixed(2)}ms`);
                            
                            // 서버에서 반환한 소요 시간 (있을 경우)
                            if (data.elapsed_time) {
                                console.log(`서버 측 DB 전환 시간: ${data.elapsed_time * 1000}ms`);
                            }
                            
                            // 시각적 피드백을 위해 약간의 지연 적용 (너무 빠르면 사용자가 변화를 인지하지 못함)
                            setTimeout(() => {
                                // 성공 메시지 표시
                                addSystemMessage(`메뉴가 '${selectedDBName}'로 변경되었습니다.`);
                                
                                // DB 전환 상태 해제
                                isChangingDB = false;
                                
                                // UI 재활성화
                                userInput.disabled = false;
                                sendBtn.disabled = false;
                            }, messageDisplayDelay);
                        } else {
                            throw new Error(data.message || '메뉴 변경 중 오류가 발생했습니다.');
                        }
                    } catch (error) {
                        console.error('DB 변경 오류:', error);
                        addErrorMessage(error.message);
                        
                        // 오류 발생 시에도 상태 및 UI 복원
                        isChangingDB = false;
                        userInput.disabled = false;
                        sendBtn.disabled = false;
                    }
                }
            });
        });
    } else {
        console.error('DB 라디오 버튼을 찾을 수 없습니다');
    }
});