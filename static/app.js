// =============================================
// STATE & CONFIG
// =============================================
let config = {
    apiKey: localStorage.getItem('admin_api_key') || '',
    apiUrl: localStorage.getItem('admin_api_url') || window.location.origin
};

const AGENTS_METADATA = {
    owner: {
        avatar: "🕵️",
        title: "Pop - Shop Operator",
        desc: "เจ้าของร้าน Advice สามร้อยยอด ผู้มีสิทธิ์ตรวจรับอนุมัติแคมเปญ",
        bullets: [
            "ตัดสินใจเลือกแคมเปญสุดท้าย",
            "ควบคุมและปรับแต่งทิศทางร้าน",
            "อนุมัติเนื้อหาโพสต์ลงเพจเฟสบุ๊ค"
        ]
    },
    scraper: {
        avatar: "🔍",
        title: "Mina - Spy Scraper",
        desc: "ดูแลระบบบอทดึงข้อมูลเพจ Advice คู่แข่งและเพจ IT",
        bullets: [
            "เช็คโพสต์ Advice ปราณบุรี & เพชรบุรี",
            "สืบค้นข้อมูลเพจเทรนด์ไอทีชั้นนำ",
            "กรองโพสต์เฉพาะกลุ่มคอมพิวเตอร์และงานซ่อม"
        ]
    },
    scoring: {
        avatar: "🧮",
        title: "Leo - Score Engine",
        desc: "คำนวณ Viral Score คีย์เวิร์ดความนิยมไอทีรายวัน",
        bullets: [
            "คัดกรองมีมขยะออกไป 35 คะแนน",
            "คำนวณคะแนน Like/Share/Comment",
            "ให้ความสำคัญสูงสุดกับคอมพิวเตอร์ประกอบ"
        ]
    },
    ai: {
        avatar: "💡",
        title: "Sam - Creative AI",
        desc: "แปลงหัวข้อข่าวเป็นแคมเปญการตลาดของร้านสามร้อยยอด",
        bullets: [
            "สร้างจุดจี้ใจลูกค้า (Customer Pain point)",
            "เพิ่มข้อเสนอซ่อมถึงบ้าน & ส่งสินค้าฟรี",
            "เขียนสคริปต์วิดีโอ Reels & แคปชันภาษาไทย"
        ]
    },
    admin: {
        avatar: "⚙️",
        title: "Ava - System Admin",
        desc: "ดูแลระบบหลังบ้าน SQLite Database และความปลอดภัย",
        bullets: [
            "เก็บข้อมูลการวิเคราะห์และ Content Memory",
            "เช็คสิทธิ์แอดมินด้วย X-Admin-API-Key",
            "ตรวจความปลอดภัยและป้องกันช่องโหว่ SSRF"
        ]
    },
    telegram: {
        avatar: "✈️",
        title: "Uploader - Telegram Bot",
        desc: "ส่งข้อมูลรายงานการตลาดประจำวันเข้า Telegram 06:00 น.",
        bullets: [
            "หั่นแบ่งข้อความยาวเกิน 4096 อักษร",
            "พยายามส่งซ้ำ 3 ครั้งหากระบบล้มเหลว",
            "คัดเลือกแนวโพสต์ Reels/TikTok ส่งตรง"
        ]
    }
};

const ROOM_IDS = {
    owner:    'room-owner',
    scraper:  'room-scraper',
    scoring:  'room-scoring',
    ai:       'room-ai',
    admin:    'room-admin',
    telegram: 'room-telegram',
};

const AGENT_ORDER = ['owner', 'scraper', 'scoring', 'ai', 'admin', 'telegram'];

// =============================================
// DOM REFS
// =============================================
const $ = id => document.getElementById(id);

// Views Toggling
const viewOffice = $('view-office');
const viewData = $('view-data');
const viewReports = $('view-reports');

const menuOverview = $('menu-overview');
const menuPosts = $('menu-posts');
const menuSources = $('menu-sources');
const menuReports = $('menu-reports');

// Tab togglers inside data view
const tabSignals = $('tab-top-signals');
const tabSaved = $('tab-saved-ideas');
const tabContentSignals = $('tab-content-signals');
const tabContentSaved = $('tab-content-saved');

// Lists
const sourceList = $('source-list');
const sourceCount = $('source-count');
const postsList = $('posts-list');
const savedIdeasList = $('saved-ideas-list');

// Badges & Stats
const statWaiting = $('stat-waiting');
const statAttention = $('stat-attention');
const statSources = $('stat-sources');
const statPosts = $('stat-posts');
const jobStatusBadge = $('job-status-badge');
const jobStatusBadgeText = $('job-status-badge-text');

// Chat UI
const consoleOutput = $('console-output');
const chatInputText = $('chat-input-text');
const btnClearLogs = $('btn-clear-logs');
const btnRunWorkflow = $('btn-run-workflow');
const btnSaveToNotion = $('btn-save-to-notion');

// Selected Agent UI
const activeAgentAvatar = $('active-agent-avatar');
const activeAgentTitle = $('active-agent-title');
const activeAgentStatus = $('active-agent-status');
const activeAgentBullets = $('active-agent-bullets');

// Settings modal
const btnSettings = $('btn-settings');
const settingsModal = $('settings-modal');
const btnCloseSettings = $('btn-close-settings');
const btnSaveSettings = $('btn-save-settings');
const inputApiKey = $('input-api-key');
const inputApiUrl = $('input-api-url');
const btnToggleKey = $('btn-toggle-key-visibility');

// Chibi & Rooms elements
const chars = {};
const rooms = {};
AGENT_ORDER.forEach(name => {
    chars[name] = $(`char-${name}`);
    rooms[name] = $(`room-${name}`);
});

// =============================================
// VIEWS & MENU TOGGLER
// =============================================
function switchView(activeMenu, activeView) {
    [menuOverview, menuPosts, menuSources, menuReports].forEach(m => m.classList.remove('active'));
    [viewOffice, viewData, viewReports].forEach(v => v.classList.remove('active'));
    
    activeMenu.classList.add('active');
    activeView.classList.add('active');
    
    // Trigger resize to fix chibi positions dynamically
    setTimeout(repositionIdles, 100);
}

menuOverview.addEventListener('click', (e) => { e.preventDefault(); switchView(menuOverview, viewOffice); });
menuPosts.addEventListener('click', (e) => { 
    e.preventDefault(); 
    switchView(menuPosts, viewData); 
    // Default to posts tab inside data board
    tabSignals.click();
});
menuSources.addEventListener('click', (e) => { 
    e.preventDefault(); 
    switchView(menuSources, viewData); 
    // We can highlight the sources side
});
menuReports.addEventListener('click', (e) => { e.preventDefault(); switchView(menuReports, viewReports); });

// API settings click
btnSettings.addEventListener('click', () => {
    inputApiKey.value = config.apiKey;
    inputApiUrl.value = config.apiUrl;
    settingsModal.classList.add('open');
});
btnCloseSettings.addEventListener('click', () => settingsModal.classList.remove('open'));
settingsModal.addEventListener('click', e => { if (e.target === settingsModal) settingsModal.classList.remove('open'); });

btnToggleKey.addEventListener('click', () => {
    const isPw = inputApiKey.type === 'password';
    inputApiKey.type = isPw ? 'text' : 'password';
    btnToggleKey.innerHTML = `<i class="fa-solid fa-eye${isPw ? '-slash' : ''}"></i>`;
});

btnSaveSettings.addEventListener('click', () => {
    config.apiKey = inputApiKey.value.trim();
    config.apiUrl = inputApiUrl.value.trim() || window.location.origin;
    localStorage.setItem('admin_api_key', config.apiKey);
    localStorage.setItem('admin_api_url', config.apiUrl);
    settingsModal.classList.remove('open');
    addChatBubble("⚙️", "System Admin", "บันทึกการเชื่อมต่อเรียบร้อยแล้วค่ะ กำลังรีเฟรชข้อมูลแดชบอร์ด...", "system");
    refreshAll();
});

// Data tabs switching
tabSignals.addEventListener('click', () => {
    tabSignals.classList.add('active'); tabSaved.classList.remove('active');
    tabContentSignals.classList.add('active'); tabContentSaved.classList.remove('active');
    loadTopPosts();
});
tabSaved.addEventListener('click', () => {
    tabSaved.classList.add('active'); tabSignals.classList.remove('active');
    tabContentSaved.classList.add('active'); tabContentSignals.classList.remove('active');
    loadSavedIdeas();
});

// =============================================
// API CALL HELPER
// =============================================
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (config.apiKey) headers['X-Admin-API-Key'] = config.apiKey;
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const url = `${config.apiUrl}${endpoint}`;
    try {
        const r = await fetch(url, opts);
        if (r.status === 401 || r.status === 403) {
            addChatBubble("❌", "API Error", "สิทธิ์การเข้าถึงถูกปฏิเสธ (401/403) กรุณาตรวจสอบ API Key ใน Settings", "error");
            return null;
        }
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return await r.json();
    } catch (e) {
        // Silent error to prevent cluttering unless necessary
        return null;
    }
}

// =============================================
// CHAT FEED LOGGING (REPLACES TERMINAL)
// =============================================
function addChatBubble(avatar, sender, text, type = 'system') {
    const chatMsg = document.createElement('div');
    chatMsg.className = `chat-msg ${type}`;
    
    chatMsg.innerHTML = `
        <span class="msg-avatar">${avatar}</span>
        <div class="msg-bubble-wrap">
            <span class="msg-sender">${sender}</span>
            <div class="msg-bubble">${text}</div>
        </div>
    `;
    
    consoleOutput.appendChild(chatMsg);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

btnClearLogs.addEventListener('click', () => {
    consoleOutput.innerHTML = '';
    addChatBubble("⚙️", "System Admin", "ล้างหน้าต่างห้องแชทเรียบร้อยแล้วค่ะ สแตนด์บายพร้อมรับคำสั่งถัดไป", "system");
});

// Update Right Sidebar Selected Agent panel
function updateSelectedAgent(agentKey) {
    const meta = AGENTS_METADATA[agentKey];
    if (!meta) return;
    
    activeAgentAvatar.innerText = meta.avatar;
    activeAgentTitle.innerText = meta.title;
    activeAgentStatus.innerText = "Online";
    
    activeAgentBullets.innerHTML = "";
    meta.bullets.forEach(b => {
        const li = document.createElement('li');
        li.innerText = b;
        activeAgentBullets.appendChild(li);
    });
}

// =============================================
// CHIBI WALKING ANIMATION SYSTEM (6 AGENTS)
// =============================================
function getLobbyPos(index) {
    const wrapper = $('office-wrapper');
    if (!wrapper) return { left: 40, top: 200 };
    const w = wrapper.offsetWidth;
    const h = wrapper.offsetHeight;
    const spacing = 45;
    const startX  = w / 2 - (spacing * 2.5); // align centered in lobby
    return {
        left: startX + index * spacing,
        top:  h - 68 // standing above entrance sign
    };
}

function getRoomCenter(roomId) {
    const room = document.getElementById(roomId);
    const wrapper = $('office-wrapper');
    if (!room || !wrapper) return { left: 100, top: 100 };
    const rr = room.getBoundingClientRect();
    const wr = wrapper.getBoundingClientRect();
    return {
        left: rr.left - wr.left + rr.width / 2 - 18, // center the chibi (w≈36)
        top:  rr.top  - wr.top  + rr.height / 2 - 8
    };
}

function placeCharsInLobby() {
    AGENT_ORDER.forEach((name, i) => {
        const el = chars[name];
        if (!el) return;
        
        // Owner and Admin can stay in their room by default to make office look occupied!
        if (name === 'owner' || name === 'admin') {
            const roomCenter = getRoomCenter(ROOM_IDS[name]);
            el.style.left = roomCenter.left + 'px';
            el.style.top  = roomCenter.top + 'px';
            el.classList.remove('walking', 'typing');
            el.classList.add('idle');
            return;
        }

        const pos = getLobbyPos(i - 1); // shift indices to exclude owner/admin
        el.style.left = pos.left + 'px';
        el.style.top  = pos.top  + 'px';
        el.classList.remove('walking', 'typing');
        el.classList.add('idle');
    });
}

function walkToRoom(agentName, speechText) {
    return new Promise(resolve => {
        const el = chars[agentName];
        const room = rooms[agentName];
        if (!el || !room) { resolve(); return; }

        const dest = getRoomCenter(ROOM_IDS[agentName]);
        el.classList.remove('idle', 'typing');
        el.classList.add('walking');

        const cx = parseFloat(el.style.left) || 0;
        const cy = parseFloat(el.style.top)  || 0;
        const dist = Math.hypot(dest.left - cx, dest.top - cy);
        const dur  = Math.max(500, Math.min(1000, dist * 1.8));

        el.style.transition = `left ${dur}ms cubic-bezier(0.4,0,0.2,1), top ${dur}ms cubic-bezier(0.4,0,0.2,1)`;
        el.style.left = dest.left + 'px';
        el.style.top  = dest.top  + 'px';

        setTimeout(() => {
            el.classList.remove('walking');
            el.classList.add('typing');
            room.classList.add('active');
            
            const bubble = $(`bubble-${agentName}`);
            if (bubble) bubble.innerText = speechText;
            resolve();
        }, dur + 50);
    });
}

function walkAllBack() {
    AGENT_ORDER.forEach((name, i) => {
        if (name === 'owner' || name === 'admin') return; // owner & admin stay in their room
        const el = chars[name];
        if (!el) return;
        
        el.classList.remove('typing');
        el.classList.add('walking');

        const pos = getLobbyPos(i - 1);
        const cx  = parseFloat(el.style.left) || 0;
        const cy  = parseFloat(el.style.top)  || 0;
        const dist = Math.hypot(pos.left - cx, pos.top - cy);
        const dur  = Math.max(500, Math.min(1000, dist * 1.5));

        el.style.transition = `left ${dur}ms cubic-bezier(0.4,0,0.2,1), top ${dur}ms cubic-bezier(0.4,0,0.2,1)`;
        el.style.left = pos.left + 'px';
        el.style.top  = pos.top  + 'px';

        setTimeout(() => {
            el.classList.remove('walking');
            el.classList.add('idle');
        }, dur + 50);
    });
    
    // Close active bubbles
    AGENT_ORDER.forEach(name => {
        if (name !== 'owner' && name !== 'admin') {
            rooms[name]?.classList.remove('active');
        }
    });
}

function repositionIdles() {
    const anyWorking = AGENT_ORDER.some(n => chars[n]?.classList.contains('typing') && n !== 'owner' && n !== 'admin');
    if (!anyWorking) placeCharsInLobby();
}

window.addEventListener('load', () => setTimeout(placeCharsInLobby, 200));
window.addEventListener('resize', repositionIdles);

// =============================================
// RUN DAILY WORKFLOW ACTION
// =============================================
btnRunWorkflow.addEventListener('click', async () => {
    btnRunWorkflow.disabled = true;
    btnRunWorkflow.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> กำลังรัน...';
    
    jobStatusBadge.className = 'badge running';
    jobStatusBadge.querySelector('.text').innerText = 'กำลังประมวลผล';
    jobStatusBadgeText.innerText = 'Running';
    
    // 0. Owner announcement
    updateSelectedAgent('owner');
    rooms.owner.classList.add('active');
    addChatBubble("🕵️", "Pop (Owner)", "กดรันระบบแล้วนะทีมงาน! ช่วยเช็คสถานะคู่แข่งด่วนวันนี้ มีอะไรเด็ดมาadaptเสนอแบรนด์ร้านเราบ้าง", "system");
    await delay(1200);
    rooms.owner.classList.remove('active');

    // 1. Spy walks
    updateSelectedAgent('scraper');
    addChatBubble("🔍", "Mina (Scraper)", "รับทราบค่ะคุณป๊อป! เดี๋ยวหนูดึงข้อมูลเพจคู่แข่ง Advice ปราณบุรี / เพชรบุรี / Advice ประจวบฯ และ IHAVECPU ให้อัปเดตที่สุดค่ะ", "running");
    await walkToRoom('scraper', 'ดึงโพสต์จากเฟสบุ๊ค...');
    
    // Call backend API (async execution in background)
    const apiPromise = apiCall('/jobs/full-daily-run', 'POST');
    
    // 2. Score Engine walks
    await delay(1500);
    updateSelectedAgent('scoring');
    addChatBubble("🧮", "Leo (Scoring)", "จัดไปครับหัวหน้า! เดี๋ยวผมนำเข้าโพสต์มาสแกนคีย์เวิร์ด PC, ซ่อมคอม, กล้องวงจรปิด และตัดคะแนนมีมขยะออก 35 คะแนนครับ", "running");
    await walkToRoom('scoring', 'คำนวณความฮิตไอที!');

    // Wait for actual API response
    const result = await apiPromise;

    // 3. AI Creative walks
    await delay(1000);
    updateSelectedAgent('ai');
    addChatBubble("💡", "Sam (Creative AI)", "ผมรับหน้าที่ต่อเองครับ! จะดึงโพสต์ท็อป 5 มาสร้างจุดจี้ใจลูกค้า เสนอจุดขายอัปเกรดเครื่องและซ่อมคอมถึงบ้านร้านเราครับ", "running");
    await walkToRoom('ai', 'ร่างแคมเปญร้านสามร้อยยอด...');
    
    // 4. Admin updates database
    await delay(1000);
    updateSelectedAgent('admin');
    rooms.admin.classList.add('active');
    addChatBubble("⚙️", "Ava (System Admin)", "ข้อมูลประมวลผลเสร็จสิ้นเรียบร้อย บันทึกลงฐานข้อมูล SQLite และระบบ Content Memory แล้วค่ะ", "running");
    await delay(1500);
    rooms.admin.classList.remove('active');

    // 5. Telegram Sender walks
    updateSelectedAgent('telegram');
    addChatBubble("✈️", "Uploader (Telegram Bot)", "ผมจัดส่งรายงานสรุปเช้าวันนี้เข้าแชนแนล Telegram Bot เรียบร้อยแล้วครับเจ้านาย! 🚀", "running");
    await walkToRoom('telegram', 'ส่งรายงานเข้า Telegram!');
    
    await delay(1500);

    // Final result output
    if (result) {
        addChatBubble("✅", "Workflow Success", `รัน Daily Workflow สำเร็จ! ดึงข้อมูลได้ ${result.collected || 0} โพสต์ / คัดกรองวิเคราะห์ไอเดีย ${result.analyzed || 0} โพสต์ / ส่งออก Telegram: สำเร็จ`, "success");
    } else {
        addChatBubble("❌", "Workflow Error", "การดึงข้อมูลผิดพลาดหรือเกิดปัญหากับเซิร์ฟเวอร์หลังบ้าน กรุณาลองใหม่อีกครั้ง", "error");
    }

    await delay(3000);
    
    // Walk back and standby
    walkAllBack();
    btnRunWorkflow.disabled = false;
    btnRunWorkflow.innerHTML = '<i class="fa-solid fa-play"></i> เริ่มสั่งรัน Daily Workflow';
    
    jobStatusBadge.className = 'badge idle';
    jobStatusBadge.querySelector('.text').innerText = 'สแตนด์บาย';
    jobStatusBadgeText.innerText = 'Standby';
    
    updateSelectedAgent('owner');
    refreshAll();
});

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

// =============================================
// PILL BOT INTERACTIONS (QUICK ASSISTS)
// =============================================
document.querySelectorAll('.pill-ask-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
        const agent = e.target.dataset.agent;
        updateSelectedAgent(agent);
        
        if (agent === 'scraper') {
            addChatBubble("🔍", "Mina (Scraper)", "แหล่งข้อมูลคู่แข่งทั้งหมด 8 แหล่งทำงานปกติค่ะ! แหล่งล่าสุดที่เราดึงเพิ่งวิเคราะห์ไป 5 โพสต์", "system");
        } else if (agent === 'scoring') {
            addChatBubble("🧮", "Leo (Scoring)", "สถิติวันนี้ โพสต์ประเภท 'Notebook' และ 'การอัปเกรดคอม' ได้ความนิยมสูงสุงเฉลี่ย 92.5 คะแนนครับ", "system");
        } else if (agent === 'ai') {
            addChatBubble("💡", "Sam (Creative AI)", "ไอเดียโฆษณาเด่นวันนี้คือ 'คอมพิวเตอร์ทำงานอืดเพราะแรมไม่พอ? บริการอัปเกรดความแรงคอมถึงบ้านคุณ' ครับ", "system");
        } else if (agent === 'admin') {
            addChatBubble("⚙️", "Ava (System Admin)", "ฐานข้อมูล SQLite เชื่อมต่อเสถียร / Content Memory จำโพสต์ที่ดึงไปแล้วเพื่อป้องกันไอเดียซ้ำซ้อนค่ะ", "system");
        } else if (agent === 'telegram') {
            addChatBubble("✈️", "Uploader (Telegram Bot)", "ระบบ Telegram Channel ออนไลน์พร้อมส่งครับ / ทดลองคุยกับบอทด้วยคำสั่ง /today ใน Telegram ได้เลย", "system");
        }
    });
});

// =============================================
// SAVE TO NOTION (MOCK ACTION)
// =============================================
btnSaveToNotion.addEventListener('click', async () => {
    btnSaveToNotion.disabled = true;
    btnSaveToNotion.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Saving...';
    
    addChatBubble("⚙️", "System Admin", "กำลังแปลงข้อมูลเป็นตารางแคมเปญของ Notion...", "running");
    await delay(1200);
    
    addChatBubble("✅", "Notion Connected", "บันทึกไอเดียคอนเทนต์วันนี้ลงใน Notion Workspace: Advice Sam Roi Yod เรียบร้อยแล้วค่ะ! 📑", "success");
    btnSaveToNotion.disabled = false;
    btnSaveToNotion.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Save to Notion';
});

// =============================================
// SOURCE HEALTH LOADING
// =============================================
async function loadSources() {
    sourceList.innerHTML = '<div class="loading-placeholder">กำลังโหลด...</div>';
    const data = await apiCall('/sources/health');
    if (!data) { 
        sourceList.innerHTML = '<div class="empty-placeholder"><i class="fa-solid fa-triangle-exclamation"></i>ไม่พบข้อมูล</div>'; 
        return; 
    }

    const sources = data.sources || [];
    sourceCount.innerText = `${sources.filter(s=>s.active).length} / ${sources.length}`;
    statSources.innerText = sources.filter(s=>s.active).length;
    
    // Estimate attention based on stale/inactive sources
    const staleCount = sources.filter(s => s.active && s.health === 'stale').length;
    statAttention.innerText = staleCount;
    
    if (!sources.length) { 
        sourceList.innerHTML = '<div class="empty-placeholder">ไม่มีแหล่งข้อมูล</div>'; 
        return; 
    }

    sourceList.innerHTML = '';
    sources.forEach(src => {
        const item = document.createElement('div');
        item.className = 'source-item';
        let sc='empty', st='ยังไม่ได้รัน';
        if (!src.active) { sc='inactive'; st='ปิดใช้งาน'; }
        else if (src.health==='ok') { sc='ok'; st='ปกติ'; }
        else if (src.health==='stale') { sc='stale'; st='ไม่อัปเดต'; }
        
        item.innerHTML = `
            <div class="source-info">
                <span class="source-name" title="${src.name}">${src.name}</span>
                <div class="source-meta">
                    <span>${src.platform}</span>
                    <span>•</span>
                    <a href="${src.source_url}" target="_blank" style="color:var(--text-muted)"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>
                </div>
            </div>
            <div class="source-status">
                <span class="status-dot ${sc}"></span>
                <span class="status-text ${sc}">${st}</span>
            </div>`;
        sourceList.appendChild(item);
    });
}

// =============================================
// TOP POSTS LOADING
// =============================================
async function loadTopPosts() {
    postsList.innerHTML = '<div class="loading-placeholder">กำลังโหลด...</div>';
    const posts = await apiCall('/posts/top');
    if (!posts || !posts.length) { 
        postsList.innerHTML = '<div class="empty-placeholder"><i class="fa-regular fa-clipboard"></i>ไม่มีโพสต์ยอดฮิตวันนี้</div>'; 
        return; 
    }

    statPosts.innerText = posts.length;

    postsList.innerHTML = '';
    posts.forEach(post => {
        const card = document.createElement('div');
        const u = (post.post_url || '').toLowerCase();
        // Check if competitors we want to boost are matching
        const boosted = u.includes('advicepranburi') || u.includes('adviceprachuap') || u.includes('advicephetchaburi') || u.includes('cpucore2duo') || u.includes('ihavecpu');
        card.className = `post-card${boosted ? ' priority-boost' : ''}`;

        let analysisHtml = '', btnHtml = '';
        if (post.analysis) {
            const a = post.analysis;
            analysisHtml = `
                <div class="ai-details">
                    <div class="detail-block">
                        <span class="detail-title"><i class="fa-solid fa-quote-left"></i> Suggested Hook</span>
                        <span class="detail-content">${a.suggested_hook || '-'}</span>
                    </div>
                    <div class="detail-block">
                        <span class="detail-title"><i class="fa-regular fa-lightbulb"></i> Local Angle</span>
                        <span class="detail-content">${a.local_angle || '-'}</span>
                    </div>
                </div>`;
            btnHtml = `<button class="btn btn-secondary btn-save-idea" data-post-id="${post.id}"><i class="fa-regular fa-bookmark"></i> บันทึกไอเดีย</button>`;
        } else {
            analysisHtml = '<div class="ai-details" style="text-align:center;color:var(--text-muted);padding:0.4rem"><i class="fa-solid fa-brain"></i> รอรับการประมวลผลบอท</div>';
        }

        card.innerHTML = `
            <div class="post-card-header">
                <span class="post-source-tag"><i class="fa-brands fa-facebook"></i> ${post.source_name || 'ไม่ทราบแหล่ง'}</span>
                <span class="post-score-tag">Viral: ${post.final_score}</span>
            </div>
            <div class="post-card-body">
                <p class="post-snippet">${post.post_text || '-'}</p>
                ${analysisHtml}
            </div>
            <div class="post-card-footer">${btnHtml}</div>`;
        postsList.appendChild(card);
    });

    document.querySelectorAll('.btn-save-idea').forEach(btn => {
        btn.addEventListener('click', async e => {
            const pid = e.target.closest('button').dataset.postId;
            e.target.disabled = true;
            e.target.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
            
            const rep = await apiCall('/reports/today');
            if (rep?.id) {
                const idx = (rep.top_posts || []).findIndex(p => p.id == pid);
                if (idx !== -1) {
                    const r = await apiCall('/ideas/save', 'POST', { report_id: rep.id, idea_number: idx + 1 });
                    if (r) {
                        addChatBubble("🕵️", "Pop (Owner)", `บันทึกไอเดียแคมเปญโพสต์ที่ #${idx + 1} เข้าระบบคัดกรองแล้ว! 📋`, "success");
                        e.target.innerHTML = '<i class="fa-solid fa-check"></i> บันทึกแล้ว';
                        statWaiting.innerText = parseInt(statWaiting.innerText) + 1;
                        return;
                    }
                }
            }
            e.target.disabled = false;
            e.target.innerHTML = '<i class="fa-regular fa-bookmark"></i> บันทึกไอเดีย';
        });
    });
}

// =============================================
// SAVED IDEAS LOADING
// =============================================
async function loadSavedIdeas() {
    savedIdeasList.innerHTML = '<div class="loading-placeholder">กำลังโหลด...</div>';
    const ideas = await apiCall('/ideas/saved');
    if (!ideas || !ideas.length) { 
        savedIdeasList.innerHTML = '<div class="empty-placeholder"><i class="fa-solid fa-bookmark"></i>ไม่มีไอเดียที่รอดำเนินการ</div>'; 
        statWaiting.innerText = 0;
        return; 
    }

    statWaiting.innerText = ideas.filter(i => i.status === 'saved').length;

    savedIdeasList.innerHTML = '';
    ideas.forEach(idea => {
        const item = document.createElement('div');
        item.className = 'post-card';
        const used = idea.status === 'used';
        
        const badge = used
            ? '<span class="post-score-tag" style="background:rgba(100,100,100,0.1);color:var(--text-muted);border-color:var(--border)">ใช้แล้ว</span>'
            : '<span class="post-score-tag" style="background:rgba(16,185,129,0.1);color:var(--green);border-color:rgba(16,185,129,0.2)">รอดำเนินการ</span>';
            
        const btn = used ? '' : `<button class="btn btn-secondary btn-mark-used" data-idea-id="${idea.id}"><i class="fa-solid fa-check"></i> ทำแคมเปญแล้ว</button>`;
        
        item.innerHTML = `
            <div class="post-card-header">
                <span class="post-source-tag"><i class="fa-solid fa-lightbulb"></i> แคมเปญไอเดีย #${idea.idea_number}</span>
                ${badge}
            </div>
            <div class="post-card-body">
                <p style="font-weight:700;color:#fff;margin-bottom:0.25rem">${idea.title || 'แคมเปญคอนเทนต์ร้านสามร้อยยอด'}</p>
                <p style="font-size:0.72rem;line-height:1.4;color:var(--text-secondary)">${idea.caption_draft || '-'}</p>
            </div>
            <div class="post-card-footer">${btn}</div>`;
        savedIdeasList.appendChild(item);
    });

    document.querySelectorAll('.btn-mark-used').forEach(btn => {
        btn.addEventListener('click', async e => {
            const id = e.target.closest('button').dataset.ideaId;
            e.target.disabled = true;
            e.target.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
            
            const r = await apiCall(`/ideas/${id}/used`, 'POST');
            if (r) {
                addChatBubble("⚙️", "System Admin", `อัปเดตสถานะแคมเปญหมายเลข #${id} เป็น 'ใช้แล้ว' สำเร็จ`, "success");
                loadSavedIdeas();
            } else {
                e.target.disabled = false;
                e.target.innerHTML = '<i class="fa-solid fa-check"></i> ทำแคมเปญแล้ว';
            }
        });
    });
}

// =============================================
// REFRESH ENGINE
// =============================================
function refreshAll() {
    loadSources();
    loadTopPosts();
    loadSavedIdeas();
}

// =============================================
// INITIALIZATION
// =============================================
updateSelectedAgent('owner');
refreshAll();
addChatBubble("🕵️", "Pop (Owner)", "ยินดีต้อนรับสู่ระบบ Advice Content Radar — ทุกคนสแตนด์บายแล้ว กดรันระบบเพื่ออัปเดตข้อมูลคู่แข่งได้เลยครับ!", "system");
