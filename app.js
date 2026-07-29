// 全域變數
let gamesData = [];
let filteredGames = [];
let currentCategory = 'all';
let currentGrade = 'all';
let currentTerm = 'all';
let currentUnit = 'all';
let currentSearch = '';

// DOM 元素
const gamesGrid = document.getElementById('gamesGrid');
const categoryList = document.getElementById('categoryList');
const gradeFilter = document.getElementById('gradeFilter');
const termFilter = document.getElementById('termFilter');
const unitFilter = document.getElementById('unitFilter');
const searchInput = document.getElementById('searchInput');
const currentCategoryTitle = document.getElementById('currentCategoryTitle');
const gameCountText = document.getElementById('gameCountText');

// QR Code Modal 元素
const qrModal = document.getElementById('qrModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const modalGameTitle = document.getElementById('modalGameTitle');
const qrcodeContainer = document.getElementById('qrcode');
const modalGameLink = document.getElementById('modalGameLink');
let currentQRCode = null;

// Slides 元素
const slidesIframe = document.getElementById('slidesIframe');
const emptyState = document.querySelector('.empty-state');
const settingsPanel = document.getElementById('settingsPanel');
const editSlidesBtn = document.getElementById('editSlidesBtn');
const setupSlidesBtn = document.getElementById('setupSlidesBtn');
const cancelSettingsBtn = document.getElementById('cancelSettingsBtn');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const slidesUrlInput = document.getElementById('slidesUrlInput');

// 啟動應用程式
document.addEventListener('DOMContentLoaded', initApp);

function initApp() {
    try {
        // 從 data.js 中載入全域變數
        if (window.gamesData) {
            gamesData = window.gamesData;
        } else {
            throw new Error("找不到 window.gamesData，請確認 data.js 是否載入成功。");
        }
        
        // 初始設定
        updateCategoryCounts();
        populateFilterOptions();
        setupEventListeners();
        
        // 載入預設的簡報連結
        loadSlidesSettings();
        
        // 觸發初始渲染
        applyFilters();
    } catch (error) {
        console.error('無法載入遊戲資料:', error);
        gamesGrid.innerHTML = `<div class="loading"><i class='bx bx-error-circle' style="font-size:48px;color:#ef4444;margin-bottom:12px;"></i><p>資料載入失敗，請確認 data.js 存在且格式正確。</p></div>`;
    }
}

// 更新左側選單的數量標籤
function updateCategoryCounts() {
    const counts = {
        'all': gamesData.length,
        '音標遊戲': 0,
        '俗語遊戲': 0,
        '其他主題單元': 0
    };
    
    gamesData.forEach(game => {
        if (counts[game.category] !== undefined) {
            counts[game.category]++;
        }
    });
    
    document.querySelectorAll('#categoryList li').forEach(li => {
        const category = li.getAttribute('data-category');
        const badge = li.querySelector('.badge');
        if (badge && counts[category] !== undefined) {
            badge.textContent = counts[category];
        }
    });
}

// 動態產生篩選器的選項
function populateFilterOptions() {
    const grades = new Set();
    const units = new Set();
    
    gamesData.forEach(game => {
        if (game.grade && game.grade !== '不分年級') grades.add(game.grade);
        if (game.unit && game.unit !== '綜合單元') units.add(game.unit);
    });
    
    // 排序年級 (一到六)
    const gradeOrder = {'一年級':1, '二年級':2, '三年級':3, '四年級':4, '五年級':5, '六年級':6};
    const sortedGrades = Array.from(grades).sort((a, b) => gradeOrder[a] - gradeOrder[b]);
    
    // 排序單元 (第一到第十)
    const unitOrder = {'第一單元':1, '第二單元':2, '第三單元':3, '第四單元':4, '第五單元':5, '第六單元':6, '第七單元':7, '第八單元':8, '第九單元':9, '第十單元':10};
    const sortedUnits = Array.from(units).sort((a, b) => (unitOrder[a] || 99) - (unitOrder[b] || 99));
    
    // 填入年級選項
    sortedGrades.forEach(grade => {
        const option = document.createElement('option');
        option.value = grade;
        option.textContent = grade;
        gradeFilter.appendChild(option);
    });
    gradeFilter.insertAdjacentHTML('beforeend', '<option value="不分年級">不分年級</option>');
    
    // 填入單元選項
    sortedUnits.forEach(unit => {
        const option = document.createElement('option');
        option.value = unit;
        option.textContent = unit;
        unitFilter.appendChild(option);
    });
    unitFilter.insertAdjacentHTML('beforeend', '<option value="綜合單元">綜合單元</option>');
}

// 設定所有事件監聽器
function setupEventListeners() {
    // 左側類別點擊
    document.querySelectorAll('#categoryList li').forEach(li => {
        li.addEventListener('click', (e) => {
            document.querySelectorAll('#categoryList li').forEach(el => el.classList.remove('active'));
            li.classList.add('active');
            
            currentCategory = li.getAttribute('data-category');
            
            // 更新標題
            const rawTitle = li.textContent.replace(/[0-9]/g, '').trim();
            currentCategoryTitle.textContent = rawTitle;
            
            applyFilters();
        });
    });
    
    // 上方篩選器與搜尋
    gradeFilter.addEventListener('change', (e) => { currentGrade = e.target.value; applyFilters(); });
    termFilter.addEventListener('change', (e) => { currentTerm = e.target.value; applyFilters(); });
    unitFilter.addEventListener('change', (e) => { currentUnit = e.target.value; applyFilters(); });
    
    searchInput.addEventListener('input', (e) => {
        currentSearch = e.target.value.toLowerCase();
        applyFilters();
    });
    
    // QR Code Modal 關閉
    closeModalBtn.addEventListener('click', closeQRModal);
    qrModal.addEventListener('click', (e) => {
        if (e.target === qrModal) closeQRModal();
    });
    
    // 簡報設定面板
    setupSlidesBtn.addEventListener('click', () => settingsPanel.style.display = 'block');
    editSlidesBtn.addEventListener('click', () => settingsPanel.style.display = 'block');
    cancelSettingsBtn.addEventListener('click', () => settingsPanel.style.display = 'none');
    
    saveSettingsBtn.addEventListener('click', () => {
        const url = slidesUrlInput.value.trim();
        saveSlidesSettings(url);
    });

    // 響應式：切換右側簡報面板
    const toggleSlidesBtn = document.getElementById('toggleSlidesBtn');
    const sidebarRight = document.getElementById('sidebarRight');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (toggleSlidesBtn && sidebarRight && sidebarOverlay) {
        toggleSlidesBtn.addEventListener('click', () => {
            sidebarRight.classList.toggle('active');
            sidebarOverlay.classList.toggle('active');
        });
        
        sidebarOverlay.addEventListener('click', () => {
            sidebarRight.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }
}

// 核心過濾邏輯
function applyFilters() {
    filteredGames = gamesData.filter(game => {
        // 1. 類別過濾
        if (currentCategory !== 'all' && game.category !== currentCategory) return false;
        
        // 2. 年級過濾
        if (currentGrade !== 'all' && game.grade !== currentGrade) return false;
        
        // 3. 學期過濾
        if (currentTerm !== 'all' && game.term !== currentTerm) return false;
        
        // 4. 單元過濾
        if (currentUnit !== 'all' && game.unit !== currentUnit) return false;
        
        // 5. 搜尋過濾
        if (currentSearch && !game.title.toLowerCase().includes(currentSearch) && !game.path.toLowerCase().includes(currentSearch)) return false;
        
        return true;
    });
    
    gameCountText.textContent = `找到 ${filteredGames.length} 個遊戲`;
    renderGames();
}

// 渲染遊戲卡片
function renderGames() {
    if (filteredGames.length === 0) {
        gamesGrid.innerHTML = `
            <div class="loading" style="grid-column: 1 / -1; height: 300px;">
                <i class='bx bx-ghost' style="font-size: 64px; margin-bottom: 16px; color: var(--text-secondary);"></i>
                <h3>找不到符合條件的遊戲</h3>
                <p>請嘗試調整上方的篩選條件或搜尋關鍵字</p>
            </div>
        `;
        return;
    }
    
    gamesGrid.innerHTML = '';
    
    filteredGames.forEach(game => {
        const card = document.createElement('div');
        card.className = 'game-card';
        
        // 處理標籤顯示，只顯示有意義的標籤
        let tagsHtml = '';
        if (game.grade !== '不分年級') tagsHtml += `<span class="tag tag-grade">${game.grade}</span>`;
        if (game.term !== '不分學期') tagsHtml += `<span class="tag tag-term">${game.term}</span>`;
        if (game.unit !== '綜合單元') tagsHtml += `<span class="tag tag-unit">${game.unit}</span>`;
        if (tagsHtml === '') tagsHtml = `<span class="tag tag-grade">綜合練習</span>`;

        card.innerHTML = `
            <div class="game-tags">
                ${tagsHtml}
            </div>
            <h3 class="game-title" title="${game.title}">${game.title}</h3>
            <div class="card-actions">
                <button class="primary-btn qr-btn" onclick="showQRCode('${game.wordwallUrl}', '${game.title.replace(/'/g, "\\'")}')">
                    <i class='bx bx-qr-scan'></i> 學生掃碼
                </button>
                <a href="${game.wordwallUrl}" target="_blank" class="primary-btn" style="flex:1;">
                    <i class='bx bx-play-circle'></i> 測試遊戲
                </a>
            </div>
        `;
        
        gamesGrid.appendChild(card);
    });
}

// 顯示 QR Code 彈出視窗
window.showQRCode = function(url, title) {
    modalGameTitle.textContent = title;
    modalGameLink.href = url;
    
    // 清除舊的 QR Code
    qrcodeContainer.innerHTML = '';
    
    // 生成新的 QR Code
    currentQRCode = new QRCode(qrcodeContainer, {
        text: url,
        width: 250,
        height: 250,
        colorDark : "#0f172a",
        colorLight : "#ffffff",
        correctLevel : QRCode.CorrectLevel.H
    });
    
    qrModal.classList.add('active');
}

// 關閉 QR Code 彈出視窗
function closeQRModal() {
    qrModal.classList.remove('active');
}

// Slides 相關功能
function loadSlidesSettings() {
    const savedUrl = localStorage.getItem('wordwall_slides_url');
    if (savedUrl) {
        slidesUrlInput.value = savedUrl;
        applySlidesUrl(savedUrl);
    }
}

function saveSlidesSettings(url) {
    localStorage.setItem('wordwall_slides_url', url);
    settingsPanel.style.display = 'none';
    applySlidesUrl(url);
}

function applySlidesUrl(url) {
    if (!url) {
        emptyState.style.display = 'block';
        slidesIframe.style.display = 'none';
        return;
    }
    
    // 處理 Google Slides 網址轉 iframe (將 /edit... 換成 /embed...)
    let embedUrl = url;
    if (url.includes('docs.google.com/presentation/d/') && url.includes('/edit')) {
        embedUrl = url.substring(0, url.lastIndexOf('/')) + '/embed?start=false&loop=false&delayms=3000';
    }
    
    slidesIframe.src = embedUrl;
    slidesIframe.style.display = 'block';
    emptyState.style.display = 'none';
}
