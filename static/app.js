// State Management
let config = {
    apiKey: localStorage.getItem('admin_api_key') || '',
    apiUrl: localStorage.getItem('admin_api_url') || window.location.origin
};

let currentTab = 'top-signals';

// DOM Elements
const sourceList = document.getElementById('source-list');
const sourceCount = document.getElementById('source-count');
const postsList = document.getElementById('posts-list');
const savedIdeasList = document.getElementById('saved-ideas-list');
const consoleOutput = document.getElementById('console-output');
const jobStatusBadge = document.getElementById('job-status-badge');
const btnRunWorkflow = document.getElementById('btn-run-workflow');
const btnClearLogs = document.getElementById('btn-clear-logs');

const btnSettings = document.getElementById('btn-settings');
const settingsModal = document.getElementById('settings-modal');
const btnCloseSettings = document.getElementById('btn-close-settings');
const btnSaveSettings = document.getElementById('btn-save-settings');
const inputApiKey = document.getElementById('input-api-key');
const inputApiUrl = document.getElementById('input-api-url');
const btnToggleKeyVisibility = document.getElementById('btn-toggle-key-visibility');

// Agent Desks
const desks = {
    scraper: document.getElementById('desk-scraper'),
    scoring: document.getElementById('desk-scoring'),
    ai: document.getElementById('desk-ai'),
    telegram: document.getElementById('desk-telegram')
};

const bubbles = {
    scraper: document.getElementById('bubble-scraper'),
    scoring: document.getElementById('bubble-scoring'),
    ai: document.getElementById('bubble-ai'),
    telegram: document.getElementById('bubble-telegram')
};

// API Fetch Helper
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    if (config.apiKey) {
        headers['X-Admin-API-Key'] = config.apiKey;
    }

    const options = {
        method,
        headers
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    const url = `${config.apiUrl}${endpoint}`;
    try {
        const response = await fetch(url, options);
        if (response.status === 401 || response.status === 403) {
            addLog(`[ERROR] สิทธิ์การเข้าถึงถูกปฏิเสธ (401/403) กรุณาตรวจสอบ API Key ในการตั้งค่า`, 'error');
            return null;
        }
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        addLog(`[ERROR] ไม่สามารถเชื่อมต่อกับหลังบ้านได้ที่ ${url} (${error.message})`, 'error');
        return null;
    }
}

// Write to Dashboard Console log
function addLog(message, type = 'system') {
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    const now = new Date().toLocaleTimeString();
    line.innerText = `[${now}] ${message}`;
    consoleOutput.appendChild(line);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

// Clear logs
btnClearLogs.addEventListener('click', () => {
    consoleOutput.innerHTML = '';
    addLog('ล้างประวัติหน้าจอสำเร็จ');
});

// Settings Modal controls
btnSettings.addEventListener('click', () => {
    inputApiKey.value = config.apiKey;
    inputApiUrl.value = config.apiUrl;
    settingsModal.classList.add('open');
});

btnCloseSettings.addEventListener('click', () => {
    settingsModal.classList.remove('open');
});

btnToggleKeyVisibility.addEventListener('click', () => {
    if (inputApiKey.type === 'password') {
        inputApiKey.type = 'text';
        btnToggleKeyVisibility.innerHTML = '<i class="fa-solid fa-eye-slash"></i>';
    } else {
        inputApiKey.type = 'password';
        btnToggleKeyVisibility.innerHTML = '<i class="fa-solid fa-eye"></i>';
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

// Tab switching logic
const tabSignals = document.getElementById('tab-top-signals');
const tabSaved = document.getElementById('tab-saved-ideas');
const tabContentSignals = document.getElementById('tab-content-signals');
const tabContentSaved = document.getElementById('tab-content-saved');

tabSignals.addEventListener('click', () => {
    tabSignals.classList.add('active');
    tabSaved.classList.remove('active');
    tabContentSignals.classList.add('active');
    tabContentSaved.classList.remove('active');
    currentTab = 'top-signals';
    loadTopPosts();
});

tabSaved.addEventListener('click', () => {
    tabSignals.classList.remove('active');
    tabSaved.classList.add('active');
    tabContentSignals.classList.remove('active');
    tabContentSaved.classList.add('active');
    currentTab = 'saved-ideas';
    loadSavedIdeas();
});

// Fetch and Render Source Health
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
        
        let statusClass = 'empty';
        let statusText = 'ยังไม่ได้รัน';
        
        if (!src.active) {
            statusClass = 'inactive';
            statusText = 'ปิดใช้งาน';
        } else if (src.health === 'ok') {
            statusClass = 'ok';
            statusText = 'ปกติ';
        } else if (src.health === 'stale') {
            statusClass = 'stale';
            statusText = 'ข้อมูลไม่อัปเดต';
        } else if (src.health === 'empty') {
            statusClass = 'empty';
            statusText = 'ไม่มีโพสต์';
        }

        item.innerHTML = `
            <div class="source-info">
                <span class="source-name" title="${src.name}">${src.name}</span>
                <div class="source-meta">
                    <span>${src.platform}</span>
                    <span>•</span>
                    <a href="${src.source_url}" target="_blank" title="เปิดลิงก์" style="color: var(--text-secondary);"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>
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

// Fetch and Render Top Posts (Tab 1)
async function loadTopPosts() {
    postsList.innerHTML = '<div class="loading-placeholder">กำลังโหลด...</div>';
    const posts = await apiCall('/posts/top');
    if (!posts || posts.length === 0) {
        postsList.innerHTML = '<div class="empty-placeholder"><i class="fa-regular fa-clipboard"></i> ไม่มีข้อมูลโพสต์ยอดฮิตสำหรับวันนี้</div>';
        return;
    }

    postsList.innerHTML = '';
    posts.forEach((post, index) => {
        const card = document.createElement('div');
        
        // Check if the post is from boosted sources
        const urlLower = (post.post_url || '').toLowerCase();
        const isBoosted = urlLower.includes('advicepranburi') || 
                          urlLower.includes('adviceprachuapkhirikhan') || 
                          urlLower.includes('advicephetchaburi') || 
                          urlLower.includes('cpucore2duo');
                          
        card.className = `post-card ${isBoosted ? 'priority-boost' : ''}`;
        
        let snippet = post.post_text || 'ไม่มีเนื้อหาข้อความ';
        
        // Check if analysis exists
        let analysisHtml = '';
        let buttonActionHtml = '';
        
        if (post.analysis) {
            const ana = post.analysis;
            analysisHtml = `
                <div class="ai-details">
                    <div class="detail-block">
                        <span class="detail-title"><i class="fa-solid fa-quote-left"></i>Suggested Hook (พาดหัวไอเดีย)</span>
                        <span class="detail-content">${ana.suggested_hook || 'ไม่มีพาดหัวไอเดีย'}</span>
                    </div>
                    <div class="detail-block">
                        <span class="detail-title"><i class="fa-regular fa-lightbulb"></i>Local Angle (การปรับกลยุทธ์พื้นที่)</span>
                        <span class="detail-content">${ana.local_angle || 'ไม่มีแนวทาง'}</span>
                    </div>
                </div>
            `;
            buttonActionHtml = `<button class="btn btn-secondary btn-save-idea" data-post-id="${post.id}"><i class="fa-regular fa-bookmark"></i> บันทึกไอเดีย</button>`;
        } else {
            analysisHtml = `
                <div class="ai-details" style="text-align: center; color: var(--text-secondary); padding: 0.5rem 0;">
                    <i class="fa-solid fa-brain-circuit"></i> โพสต์นี้ยังไม่ถูกเลือกวิเคราะห์ด้วย AI ในสรุปวันนี้
                </div>
            `;
        }

        card.innerHTML = `
            <div class="post-card-header">
                <span class="post-source-tag"><i class="fa-brands fa-facebook"></i> ${post.source_name || 'ไม่ทราบแหล่งที่มา'}</span>
                <span class="post-score-tag">คะแนน: ${post.final_score}</span>
            </div>
            <div class="post-card-body">
                <p class="post-snippet">${snippet}</p>
                ${analysisHtml}
            </div>
            <div class="post-card-footer">
                ${buttonActionHtml}
            </div>
        `;
        postsList.appendChild(card);
    });

    // Attach Save Idea Click Event
    document.querySelectorAll('.btn-save-idea').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const postId = e.target.closest('button').dataset.postId;
            e.target.disabled = true;
            e.target.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> บันทึก...';
            
            // To save an idea, we need to call POST /ideas/save
            // We need a report_id or we can mock/fetch today's report
            const todayReport = await apiCall('/reports/today');
            if (todayReport && todayReport.id) {
                // Find matching index in report.top_posts
                const topPostsList = todayReport.top_posts || [];
                const postIndex = topPostsList.findIndex(p => p.id == postId);
                if (postIndex !== -1) {
                    // Trigger save
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
                    addLog('[WARNING] โพสต์นี้ไม่ติดอันดับวิเคราะห์หลักในรายงานวันนี้', 'system');
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

// Fetch and Render Saved Ideas (Tab 2)
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
        
        let statusBadge = '';
        let buttonAction = '';
        if (idea.status === 'used') {
            statusBadge = '<span class="post-score-tag" style="background: rgba(120,120,120,0.1); color: var(--text-secondary); border-color: var(--border-color);">ใช้โพสต์แล้ว</span>';
        } else {
            statusBadge = '<span class="post-score-tag" style="background: rgba(57,255,20,0.1); color: var(--accent-neon-green); border-color: rgba(57,255,20,0.2);">รอดำเนินการ</span>';
            buttonAction = `<button class="btn btn-secondary btn-mark-used" data-idea-id="${idea.id}"><i class="fa-solid fa-check"></i> ทำเครื่องหมายว่าใช้แล้ว</button>`;
        }

        item.innerHTML = `
            <div class="post-card-header">
                <span class="post-source-tag"><i class="fa-solid fa-lightbulb"></i> ไอเดียที่ #${idea.idea_number} (รายงาน ID: ${idea.report_id})</span>
                ${statusBadge}
            </div>
            <div class="post-card-body">
                <p style="margin-bottom: 0.5rem; font-weight: 600; color: var(--text-primary);">${idea.title || 'ไอเดียคอนเทนต์ไอที'}</p>
                <p style="font-size: 0.8rem; line-height: 1.4; color: var(--text-secondary);">${idea.caption_draft || 'ไม่มีแคปชั่นร่าง'}</p>
            </div>
            <div class="post-card-footer">
                ${buttonAction}
            </div>
        `;
        savedIdeasList.appendChild(item);
    });

    // Mark as Used Action Event
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

// 8-Bit Agent Desk Activation Controller
function resetAgentDesks() {
    Object.keys(desks).forEach(k => {
        desks[k].classList.remove('active');
    });
}

function activateAgent(agentName, textBubble) {
    resetAgentDesks();
    if (desks[agentName]) {
        desks[agentName].classList.add('active');
        if (bubbles[agentName]) {
            bubbles[agentName].innerText = textBubble;
        }
    }
}

// Trigger Full Daily Workflow
btnRunWorkflow.addEventListener('click', async () => {
    btnRunWorkflow.disabled = true;
    btnRunWorkflow.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> กำลังวิเคราะห์ระบบ...';
    jobStatusBadge.className = 'badge running';
    jobStatusBadge.querySelector('.text').innerText = 'กำลังประมวลผล';
    
    addLog('--- เริ่มสั่งรัน Daily Workflow (แมนนวล) ---', 'running');
    
    // Step 1: Scraper Agent active (fetching posts)
    activateAgent('scraper', 'กำลังกวาดล้างและดึงเพจคู่แข่ง...');
    addLog('[Step 1/4] เรียกใช้บอทดึงข้อมูล Facebook/Web sources...', 'running');
    
    // We send a request to start the full run
    // Since it can take some time, we will run the API request
    const result = await apiCall('/jobs/full-daily-run', 'POST');
    
    if (result) {
        // Step 2: Scoring Agent active
        activateAgent('scoring', 'ประเมินความไวรัล + โลคอลบ๊อสต์!');
        addLog(`[Step 2/4] ดึงโพสต์รวมสำเร็จ ${result.collected || 0} โพสต์ กำลังส่งวิเคราะห์คะแนน...`, 'running');
        
        // Wait 1.5s to show scoring agent animation
        await new Promise(r => setTimeout(r, 1500));
        
        // Step 3: AI Writer active
        activateAgent('ai', 'ให้ AI ร่างแผนโต้ตอบการตลาดในสามร้อยยอด...');
        addLog(`[Step 3/4] คำนวณความเหมาะสมเสร็จสิ้น กำลังส่งโพสต์ท็อป ${result.analyzed || 0} รายการให้ AI ปรับสคริปต์...`, 'running');
        
        // Wait 2s to show AI writing animation
        await new Promise(r => setTimeout(r, 2000));
        
        // Step 4: Telegram active
        activateAgent('telegram', 'ยิงรายงานตรงเข้า Telegram!');
        addLog(`[Step 4/4] สร้างรายงานประจำวัน ID: ${result.report_id || 0} กำลังจัดส่งเข้าโทรศัพท์แอดมิน...`, 'running');
        
        // Wait 1.5s
        await new Promise(r => setTimeout(r, 1500));
        
        // Finalize
        resetAgentDesks();
        btnRunWorkflow.disabled = false;
        btnRunWorkflow.innerHTML = '<i class="fa-solid fa-play"></i> สั่งรัน Daily Workflow เดี๋ยวนี้';
        jobStatusBadge.className = 'badge idle';
        jobStatusBadge.querySelector('.text').innerText = 'สแตนด์บาย';
        
        addLog(`[SUCCESS] กระบวนการทั้งหมดเสร็จสมบูรณ์! ส่งเข้า Telegram สำเร็จ: ${result.telegram_sent}`, 'success');
        refreshAll();
    } else {
        resetAgentDesks();
        btnRunWorkflow.disabled = false;
        btnRunWorkflow.innerHTML = '<i class="fa-solid fa-play"></i> สั่งรัน Daily Workflow เดี๋ยวนี้';
        jobStatusBadge.className = 'badge error';
        jobStatusBadge.querySelector('.text').innerText = 'เกิดข้อผิดพลาด';
        addLog('[FAIL] การรันกระบวนการล้มเหลว กรุณาตรวจสอบบันทึกความปลอดภัยของเซิร์ฟเวอร์', 'error');
    }
});

// Refresh all components
function refreshAll() {
    loadSources();
    if (currentTab === 'top-signals') {
        loadTopPosts();
    } else {
        loadSavedIdeas();
    }
}

// Initial Loading
refreshAll();
addLog('แดชบอร์ดพร้อมทำงาน ดึงสถานะเชื่อมต่อเรียบร้อย');
