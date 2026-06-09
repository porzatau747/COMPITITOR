// =============================================
// State Management
// =============================================
let config = {
    apiKey: localStorage.getItem('admin_api_key') || '',
    apiUrl: localStorage.getItem('admin_api_url') || window.location.origin
};

let currentTab = 'top-signals';

// =============================================
// DOM Elements
// =============================================
const sourceList      = document.getElementById('source-list');
const sourceCount     = document.getElementById('source-count');
const postsList       = document.getElementById('posts-list');
const savedIdeasList  = document.getElementById('saved-ideas-list');
const consoleOutput   = document.getElementById('console-output');
const jobStatusBadge  = document.getElementById('job-status-badge');
const btnRunWorkflow  = document.getElementById('btn-run-workflow');
const btnClearLogs    = document.getElementById('btn-clear-logs');

const btnSettings         = document.getElementById('btn-settings');
const settingsModal       = document.getElementById('settings-modal');
const btnCloseSettings    = document.getElementById('btn-close-settings');
const btnSaveSettings     = document.getElementById('btn-save-settings');
const inputApiKey         = document.getElementById('input-api-key');
const inputApiUrl         = document.getElementById('input-api-url');
const btnToggleKeyVis     = document.getElementById('btn-toggle-key-visibility');

// Workstation elements (for speech bubbles)
const workstations = {
    scraper:  document.getElementById('ws-scraper'),
    scoring:  document.getElementById('ws-scoring'),
    ai:       document.getElementById('ws-ai'),
    telegram: document.getElementById('ws-telegram'),
};

// Character elements
const characters = {
    scraper:  document.getElementById('char-scraper'),
    scoring:  document.getElementById('char-scoring'),
    ai:       document.getElementById('char-ai'),
    telegram: document.getElementById('char-telegram'),
};

// =============================================
// API Fetch Helper
// =============================================
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (config.apiKey) headers['X-Admin-API-Key'] = config.apiKey;

    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    const url = `${config.apiUrl}${endpoint}`;
    try {
        const response = await fetch(url, options);
        if (response.status === 401 || response.status === 403) {
            addLog('[ERROR] สิทธิ์การเข้าถึงถูกปฏิเสธ (401/403) กรุณาตรวจสอบ API Key ในการตั้งค่า', 'error');
            return null;
        }
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        addLog(`[ERROR] ไม่สามารถเชื่อมต่อกับหลังบ้านได้ที่ ${url} (${error.message})`, 'error');
        return null;
    }
}

// =============================================
// Console Log
// =============================================
function addLog(message, type = 'system') {
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    const now = new Date().toLocaleTimeString('th-TH');
    line.innerText = `[${now}] ${message}`;
    consoleOutput.appendChild(line);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

btnClearLogs.addEventListener('click', () => {
    consoleOutput.innerHTML = '';
    addLog('ล้างประวัติหน้าจอสำเร็จ');
});

// =============================================
// Settings Modal
// =============================================
btnSettings.addEventListener('click', () => {
    inputApiKey.value = config.apiKey;
    inputApiUrl.value = config.apiUrl;
    settingsModal.classList.add('open');
});

btnCloseSettings.addEventListener('click', () => settingsModal.classList.remove('open'));
settingsModal.addEventListener('click', (e) => { if (e.target === settingsModal) settingsModal.classList.remove('open'); });

btnToggleKeyVis.addEventListener('click', () => {
    if (inputApiKey.type === 'password') {
        inputApiKey.type = 'text';
        btnToggleKeyVis.innerHTML = '<i class="fa-solid fa-eye-slash"></i>';
    } else {
        inputApiKey.type = 'password';
        btnToggleKeyVis.innerHTML = '<i class="fa-solid fa-eye"></i>';
    }
});

btnSaveSettings.addEventListener('click', () => {
    config.apiKey = inputApiKey.value.trim();
    config.apiUrl = inputApiUrl.value.trim() || window.location.origin;
    localStorage.setItem('admin_api_key', config.apiKey);
    localStorage.setItem('admin_api_url', config.apiUrl);
    settingsModal.classList.remove('open');
    addLog('บันทึกการตั้งค่าสิทธิ์เรียบร้อยแล้ว เริ่มรีโหลดข้อมูล...');
    refreshAll();
});

// =============================================
// Tab Switching
// =============================================
const tabSignals = document.getElementById('tab-top-signals');
const tabSaved   = document.getElementById('tab-saved-ideas');
const tabContentSignals = document.getElementById('tab-content-signals');
const tabContentSaved   = document.getElementById('tab-content-saved');

tabSignals.addEventListener('click', () => {
    tabSignals.classList.add('active');    tabSaved.classList.remove('active');
    tabContentSignals.classList.add('active'); tabContentSaved.classList.remove('active');
    currentTab = 'top-signals';
    loadTopPosts();
});

tabSaved.addEventListener('click', () => {
    tabSaved.classList.add('active');    tabSignals.classList.remove('active');
    tabContentSaved.classList.add('active'); tabContentSignals.classList.remove('active');
    currentTab = 'saved-ideas';
    loadSavedIdeas();
});

// =============================================
// CHARACTER / OFFICE ANIMATION SYSTEM
// =============================================

/**
 * Calculate the horizontal center of a workstation element
 * relative to the characters-layer (which spans the full width).
 */
function getWorkstationCenter(wsId) {
    const ws = document.getElementById(wsId);
    const layer = document.getElementById('characters-layer');
    if (!ws || !layer) return null;
    const wsRect    = ws.getBoundingClientRect();
    const layerRect = layer.getBoundingClientRect();
    // center of workstation relative to characters-layer left edge
    return wsRect.left + wsRect.width / 2 - layerRect.left - 10; // -10 to center char (width≈20)
}

/** Idle positions: all characters cluster in the break-room (right side) */
const IDLE_OFFSETS = {
    scraper:  -105,
    scoring:  -75,
    ai:       -45,
    telegram: -15,
};

function setCharIdlePositions() {
    const layer = document.getElementById('characters-layer');
    const layerWidth = layer ? layer.getBoundingClientRect().width : 500;
    Object.entries(IDLE_OFFSETS).forEach(([name, offset]) => {
        const el = characters[name];
        if (el) el.style.left = `${layerWidth + offset}px`;
    });
}

/**
 * Move a character to its target workstation with walking animation,
 * then show its speech bubble and switch to typing state.
 *
 * @param {string} agentName - 'scraper' | 'scoring' | 'ai' | 'telegram'
 * @param {string} speechText - text to show in speech bubble
 * @param {number} delay - ms to wait before starting the walk
 */
function walkCharacterToDesk(agentName, speechText, delay = 0) {
    return new Promise((resolve) => {
        setTimeout(() => {
            const char = characters[agentName];
            const wsId = `ws-${agentName}`;
            const ws   = workstations[agentName];

            if (!char || !ws) { resolve(); return; }

            // Compute destination
            const destX = getWorkstationCenter(wsId);
            if (destX === null) { resolve(); return; }

            // Remove other states, add walking
            char.classList.remove('idle-bounce', 'typing');
            char.classList.add('walking');

            // Compute walk duration based on distance
            const currentLeft = parseFloat(char.style.left) || 0;
            const distance    = Math.abs(currentLeft - destX);
            const duration    = Math.max(400, Math.min(1200, distance * 1.5)); // 400–1200ms

            // Animate by changing left (CSS transition handles easing)
            char.style.transition = `left ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            char.style.left = `${destX}px`;

            setTimeout(() => {
                // Arrived at desk
                char.classList.remove('walking');
                char.classList.add('typing');

                // Activate desk speech bubble
                ws.classList.add('active');
                const bubble = document.getElementById(`bubble-${agentName}`);
                if (bubble) bubble.innerText = speechText;

                resolve();
            }, duration + 50);

        }, delay);
    });
}

/** Return all characters to idle zone */
function walkAllCharactersToIdle() {
    const layer = document.getElementById('characters-layer');
    const layerWidth = layer ? layer.getBoundingClientRect().width : 500;

    Object.entries(characters).forEach(([name, el]) => {
        if (!el) return;
        el.classList.remove('typing');
        el.classList.add('walking', 'idle-bounce');

        const destX = layerWidth + IDLE_OFFSETS[name];
        const currentLeft = parseFloat(el.style.left) || destX;
        const distance = Math.abs(currentLeft - destX);
        const duration = Math.max(400, Math.min(1000, distance * 1.2));

        el.style.transition = `left ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        el.style.left = `${destX}px`;

        setTimeout(() => {
            el.classList.remove('walking');
        }, duration + 50);
    });

    // Clear all desk speech bubbles
    Object.values(workstations).forEach(ws => ws && ws.classList.remove('active'));
}

/** Reset everything to idle state */
function resetOffice() {
    walkAllCharactersToIdle();
    Object.values(workstations).forEach(ws => ws && ws.classList.remove('active'));
}

// Initialize idle positions after DOM is ready
window.addEventListener('load', () => {
    // Short delay so getBoundingClientRect works correctly
    setTimeout(() => {
        setCharIdlePositions();
        // All chars idle-bounce while waiting
        Object.values(characters).forEach(el => el && el.classList.add('idle-bounce'));
    }, 100);
});

// Also reposition on resize
window.addEventListener('resize', () => {
    setCharIdlePositions();
});

// =============================================
// RUN DAILY WORKFLOW
// =============================================
btnRunWorkflow.addEventListener('click', async () => {
    btnRunWorkflow.disabled = true;
    btnRunWorkflow.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> กำลังส่งคำสั่ง...';
    jobStatusBadge.className = 'badge running';
    jobStatusBadge.querySelector('.text').innerText = 'กำลังประมวลผล';

    addLog('━━━ เริ่มสั่งรัน Daily Workflow (แมนนวล) ━━━', 'running');

    // --- STEP 1: Scraper walks to desk ---
    addLog('[Step 1/4] 🔍 น้องสปายกำลังเดินไปที่โต๊ะเพื่อดึงข้อมูล Facebook...', 'running');
    await walkCharacterToDesk('scraper', 'กำลังดึงข้อมูลเพจ...', 0);

    // Fire the actual API call while animations continue
    const resultPromise = apiCall('/jobs/full-daily-run', 'POST');

    // --- STEP 2: Scoring walks (after brief delay) ---
    await new Promise(r => setTimeout(r, 800));
    addLog('[Step 2/4] 🧮 น้องสคอร์กำลังเดินมาช่วยคำนวณคะแนน...', 'running');
    await walkCharacterToDesk('scoring', 'คิดคะแนน viral!', 0);

    // Wait for API result
    const result = await resultPromise;

    // --- STEP 3: AI Writer walks ---
    await new Promise(r => setTimeout(r, 400));
    addLog('[Step 3/4] 💡 น้องครีเอทีฟกำลังเดินมาเขียนคอนเทนต์โต้กลับ...', 'running');
    await walkCharacterToDesk('ai', 'คิดสคริปต์แล้ว!', 0);

    await new Promise(r => setTimeout(r, 600));

    // --- STEP 4: Telegram sender walks ---
    addLog('[Step 4/4] ✈️ น้องแมสเซนเจอร์กำลังเดินไปส่งรายงานเข้า Telegram...', 'running');
    await walkCharacterToDesk('telegram', 'ส่งเข้าแชทแล้ว!', 0);

    await new Promise(r => setTimeout(r, 1000));

    // --- FINALIZE ---
    if (result) {
        addLog(`[SUCCESS] ✅ กระบวนการทั้งหมดสำเร็จ! ดึง ${result.collected || 0} โพสต์, วิเคราะห์ ${result.analyzed || 0} รายการ, รายงาน ID: ${result.report_id || 0}, ส่ง Telegram: ${result.telegram_sent ? 'สำเร็จ' : 'ไม่ส่ง'}`, 'success');
    } else {
        addLog('[FAIL] ❌ การรันกระบวนการล้มเหลว กรุณาตรวจสอบบันทึกเซิร์ฟเวอร์', 'error');
    }

    // Wait 2s so user can see the happy agents, then return to idle
    await new Promise(r => setTimeout(r, 2000));

    resetOffice();
    btnRunWorkflow.disabled = false;
    btnRunWorkflow.innerHTML = '<i class="fa-solid fa-play"></i> เริ่มสั่งรัน Daily Workflow';
    jobStatusBadge.className = 'badge idle';
    jobStatusBadge.querySelector('.text').innerText = 'สแตนด์บาย';

    refreshAll();
});

// =============================================
// SOURCE HEALTH
// =============================================
async function loadSources() {
    sourceList.innerHTML = '<div class="loading-placeholder">กำลังโหลด...</div>';
    const data = await apiCall('/sources/health');
    if (!data) {
        sourceList.innerHTML = '<div class="empty-placeholder"><i class="fa-solid fa-triangle-exclamation"></i> ไม่พบแหล่งข้อมูล</div>';
        return;
    }

    const sources = data.sources || [];
    const activeSources = sources.filter(s => s.active);
    sourceCount.innerText = `${activeSources.length} / ${sources.length}`;

    if (sources.length === 0) {
        sourceList.innerHTML = '<div class="empty-placeholder">ไม่มีแหล่งข้อมูลที่ลงทะเบียนไว้</div>';
        return;
    }

    sourceList.innerHTML = '';
    sources.forEach(src => {
        const item = document.createElement('div');
        item.className = 'source-item';

        let statusClass = 'empty', statusText = 'ยังไม่ได้รัน';
        if (!src.active)            { statusClass = 'inactive'; statusText = 'ปิดใช้งาน'; }
        else if (src.health === 'ok')     { statusClass = 'ok';       statusText = 'ปกติ'; }
        else if (src.health === 'stale')  { statusClass = 'stale';    statusText = 'ไม่อัปเดต'; }
        else if (src.health === 'empty')  { statusClass = 'empty';    statusText = 'ไม่มีโพสต์'; }

        item.innerHTML = `
            <div class="source-info">
                <span class="source-name" title="${src.name}">${src.name}</span>
                <div class="source-meta">
                    <span>${src.platform}</span>
                    <span>•</span>
                    <a href="${src.source_url}" target="_blank" style="color: var(--text-secondary);"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>
                </div>
            </div>
            <div class="source-status">
                <span class="status-dot ${statusClass}"></span>
                <span class="status-text ${statusClass}">${statusText}</span>
            </div>
        `;
        sourceList.appendChild(item);
    });
}

// =============================================
// TOP POSTS (Tab 1)
// =============================================
async function loadTopPosts() {
    postsList.innerHTML = '<div class="loading-placeholder">กำลังโหลด...</div>';
    const posts = await apiCall('/posts/top');
    if (!posts || posts.length === 0) {
        postsList.innerHTML = '<div class="empty-placeholder"><i class="fa-regular fa-clipboard"></i> ไม่มีข้อมูลโพสต์ยอดฮิตสำหรับวันนี้</div>';
        return;
    }

    postsList.innerHTML = '';
    posts.forEach((post) => {
        const card = document.createElement('div');

        const urlLower = (post.post_url || '').toLowerCase();
        const isBoosted = urlLower.includes('advicepranburi') ||
                          urlLower.includes('adviceprachuapkhirikhan') ||
                          urlLower.includes('advicephetchaburi') ||
                          urlLower.includes('cpucore2duo');

        card.className = `post-card ${isBoosted ? 'priority-boost' : ''}`;

        let analysisHtml = '';
        let buttonActionHtml = '';

        if (post.analysis) {
            const ana = post.analysis;
            analysisHtml = `
                <div class="ai-details">
                    <div class="detail-block">
                        <span class="detail-title"><i class="fa-solid fa-quote-left"></i> Suggested Hook (พาดหัวไอเดีย)</span>
                        <span class="detail-content">${ana.suggested_hook || 'ไม่มีพาดหัวไอเดีย'}</span>
                    </div>
                    <div class="detail-block">
                        <span class="detail-title"><i class="fa-regular fa-lightbulb"></i> Local Angle (การปรับกลยุทธ์พื้นที่)</span>
                        <span class="detail-content">${ana.local_angle || 'ไม่มีแนวทาง'}</span>
                    </div>
                </div>
            `;
            buttonActionHtml = `<button class="btn btn-secondary btn-save-idea" data-post-id="${post.id}"><i class="fa-regular fa-bookmark"></i> บันทึกไอเดีย</button>`;
        } else {
            analysisHtml = `
                <div class="ai-details" style="text-align:center;color:var(--text-secondary);padding:0.5rem 0;">
                    <i class="fa-solid fa-brain"></i> โพสต์นี้ยังไม่ถูกเลือกวิเคราะห์ด้วย AI ในสรุปวันนี้
                </div>
            `;
        }

        card.innerHTML = `
            <div class="post-card-header">
                <span class="post-source-tag"><i class="fa-brands fa-facebook"></i> ${post.source_name || 'ไม่ทราบแหล่งที่มา'}</span>
                <span class="post-score-tag">คะแนน: ${post.final_score}</span>
            </div>
            <div class="post-card-body">
                <p class="post-snippet">${post.post_text || 'ไม่มีเนื้อหาข้อความ'}</p>
                ${analysisHtml}
            </div>
            <div class="post-card-footer">${buttonActionHtml}</div>
        `;
        postsList.appendChild(card);
    });

    // Save idea buttons
    document.querySelectorAll('.btn-save-idea').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const postId = e.target.closest('button').dataset.postId;
            e.target.disabled = true;
            e.target.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> บันทึก...';

            const todayReport = await apiCall('/reports/today');
            if (todayReport && todayReport.id) {
                const topPostsList = todayReport.top_posts || [];
                const postIndex = topPostsList.findIndex(p => p.id == postId);
                if (postIndex !== -1) {
                    const result = await apiCall('/ideas/save', 'POST', {
                        report_id: todayReport.id,
                        idea_number: postIndex + 1
                    });
                    if (result) {
                        addLog(`บันทึกไอเดียโพสต์อันดับที่ ${postIndex + 1} เรียบร้อย!`);
                        e.target.innerHTML = '<i class="fa-solid fa-circle-check"></i> บันทึกแล้ว';
                        e.target.className = 'btn btn-secondary';
                    } else {
                        e.target.disabled = false;
                        e.target.innerHTML = '<i class="fa-regular fa-bookmark"></i> บันทึกไอเดีย';
                    }
                } else {
                    addLog('[WARNING] โพสต์นี้ไม่ติดอันดับวิเคราะห์หลักในรายงานวันนี้');
                    e.target.disabled = false;
                    e.target.innerHTML = '<i class="fa-regular fa-bookmark"></i> บันทึกไอเดีย';
                }
            } else {
                addLog('[ERROR] ไม่พบรายงานประจำวันเพื่อเชื่อมโยงไอเดีย', 'error');
                e.target.disabled = false;
                e.target.innerHTML = '<i class="fa-regular fa-bookmark"></i> บันทึกไอเดีย';
            }
        });
    });
}

// =============================================
// SAVED IDEAS (Tab 2)
// =============================================
async function loadSavedIdeas() {
    savedIdeasList.innerHTML = '<div class="loading-placeholder">กำลังโหลด...</div>';
    const ideas = await apiCall('/ideas/saved');
    if (!ideas || ideas.length === 0) {
        savedIdeasList.innerHTML = '<div class="empty-placeholder"><i class="fa-solid fa-bookmark"></i> ไม่มีไอเดียที่บันทึกไว้</div>';
        return;
    }

    savedIdeasList.innerHTML = '';
    ideas.forEach(idea => {
        const item = document.createElement('div');
        item.className = 'post-card';

        let statusBadge = '', buttonAction = '';
        if (idea.status === 'used') {
            statusBadge = '<span class="post-score-tag" style="background:rgba(120,120,120,0.1);color:var(--text-secondary);border-color:var(--border-color);">ใช้โพสต์แล้ว</span>';
        } else {
            statusBadge = '<span class="post-score-tag" style="background:rgba(57,255,20,0.1);color:var(--accent-neon-green);border-color:rgba(57,255,20,0.2);">รอดำเนินการ</span>';
            buttonAction = `<button class="btn btn-secondary btn-mark-used" data-idea-id="${idea.id}"><i class="fa-solid fa-check"></i> ทำเครื่องหมายว่าใช้แล้ว</button>`;
        }

        item.innerHTML = `
            <div class="post-card-header">
                <span class="post-source-tag"><i class="fa-solid fa-lightbulb"></i> ไอเดียที่ #${idea.idea_number} (รายงาน ID: ${idea.report_id})</span>
                ${statusBadge}
            </div>
            <div class="post-card-body">
                <p style="margin-bottom:0.5rem;font-weight:600;color:var(--text-primary);">${idea.title || 'ไอเดียคอนเทนต์ไอที'}</p>
                <p style="font-size:0.8rem;line-height:1.4;color:var(--text-secondary);">${idea.caption_draft || 'ไม่มีแคปชั่นร่าง'}</p>
            </div>
            <div class="post-card-footer">${buttonAction}</div>
        `;
        savedIdeasList.appendChild(item);
    });

    document.querySelectorAll('.btn-mark-used').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const ideaId = e.target.closest('button').dataset.ideaId;
            e.target.disabled = true;
            e.target.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> อัปเดต...';
            const result = await apiCall(`/ideas/${ideaId}/used`, 'POST');
            if (result) {
                addLog(`อัปเดตสถานะไอเดีย ID: ${ideaId} ว่าใช้โพสต์จริงเรียบร้อยแล้ว`);
                loadSavedIdeas();
            } else {
                e.target.disabled = false;
                e.target.innerHTML = '<i class="fa-solid fa-check"></i> ทำเครื่องหมายว่าใช้แล้ว';
            }
        });
    });
}

// =============================================
// REFRESH ALL PANELS
// =============================================
function refreshAll() {
    loadSources();
    if (currentTab === 'top-signals') loadTopPosts();
    else loadSavedIdeas();
}

// =============================================
// INITIAL LOAD
// =============================================
refreshAll();
addLog('แดชบอร์ดพร้อมทำงาน — พนักงานทุกคนพักรอที่ Break Room ☕');
