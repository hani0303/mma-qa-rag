/**
 * 공통 JavaScript 함수
 */

// 로딩 오버레이 표시/숨김 함수
function showLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('hidden');
    }
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('hidden');
    }
}

// 알림 표시 함수
function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    alertContainer.innerHTML = '';
    alertContainer.appendChild(alertDiv);

    // 3초 후 알림 자동 제거
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// 관리자 페이지로 이동 함수
function navigateToDocumentManager() {
    window.location.href = '/document_manager';
}

// 메인 페이지로 이동 함수
function navigateToMainPage() {
    window.location.href = '/';
}