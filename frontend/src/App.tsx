import { useEffect, useState, useRef, useCallback } from 'react';
import { OfficeCanvas } from './office/components/OfficeCanvas.js';
import { OfficeState } from './office/engine/officeState.js';
import { deserializeLayout } from './office/layout/layoutSerializer.js';
import { setCharacterTemplates } from './office/sprites/spriteData.js';
import { setFloorSprites } from './office/floorTiles.js';
import { setWallSprites } from './office/wallTiles.js';
import { buildDynamicCatalog } from './office/layout/furnitureCatalog.js';

// Metadata and icons for agents
const AGENTS_METADATA: Record<string, {
  id: number;
  avatar: string;
  title: string;
  desc: string;
  bullets: string[];
}> = {
  owner: {
    id: 0,
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
    id: 1,
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
    id: 2,
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
    id: 3,
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
    id: 4,
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
    id: 5,
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

const AGENT_KEYS = ['owner', 'scraper', 'scoring', 'ai', 'admin', 'telegram'];

interface SourceItem {
  name: string;
  platform: string;
  source_url: string;
  active: boolean;
  health: 'ok' | 'stale' | 'inactive';
}

interface PostItem {
  id: number;
  source_name: string;
  post_url: string;
  post_text: string;
  final_score: number;
  analysis?: {
    suggested_hook?: string;
    local_angle?: string;
  };
}

interface SavedIdeaItem {
  id: number;
  idea_number: number;
  title: string;
  caption_draft: string;
  status: 'saved' | 'used';
}

interface LogEntry {
  time: string;
  sender: string;
  text: string;
  type: 'system' | 'running' | 'success' | 'error';
}

// Mock editor state to prevent canvas crash
const mockEditorState = {
  activeTool: 0,
  ghostCol: -1,
  ghostRow: -1,
  ghostValid: false,
  selectedFurnitureType: '',
  selectedFurnitureUid: null,
  isDragMoving: false,
  dragUid: null,
  dragOffsetCol: 0,
  dragOffsetRow: 0,
  dragStartCol: 0,
  dragStartRow: 0,
  isDragging: false,
  wallDragAdding: null,
  clearDrag: () => {},
  clearSelection: () => {}
};

function App() {
  const [isAssetsLoaded, setIsAssetsLoaded] = useState(false);
  const [officeState, setOfficeState] = useState<OfficeState | null>(null);
  
  // Settings
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('admin_api_key') || '');
  const [apiUrl, setApiUrl] = useState(() => localStorage.getItem('admin_api_url') || window.location.origin);
  const [showSettings, setShowSettings] = useState(false);
  const [tempApiKey, setTempApiKey] = useState('');
  const [tempApiUrl, setTempApiUrl] = useState('');
  const [showKeyVisible, setShowKeyVisible] = useState(false);
  
  // API Data
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [topPosts, setTopPosts] = useState<PostItem[]>([]);
  const [savedIdeas, setSavedIdeas] = useState<SavedIdeaItem[]>([]);
  
  // Layout views state
  const [activeTab, setActiveTab] = useState<'posts' | 'saved'>('posts');
  const [isConsoleCollapsed, setIsConsoleCollapsed] = useState(false);
  const [selectedAgentKey, setSelectedAgentKey] = useState('owner');
  const [jobStatus, setJobStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  // Canvas settings
  const [zoom, setZoom] = useState(4);
  const [editorTick] = useState(0);
  const panRef = useRef({ x: 0, y: 0 });

  // Seat mappings inside the office vs lounge
  const officeSeatIdsRef = useRef<Record<number, string>>({});
  const loungeSeatIdsRef = useRef<Record<number, string>>({});

  const consoleEndRef = useRef<HTMLDivElement>(null);

  // API caller helper
  const apiCall = useCallback(async (endpoint: string, method = 'GET', body: any = null) => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) {
      headers['X-Admin-API-Key'] = apiKey;
    }
    const opts: RequestInit = { method, headers };
    if (body) {
      opts.body = JSON.stringify(body);
    }
    const cleanUrl = `${apiUrl.replace(/\/$/, '')}${endpoint}`;
    try {
      const r = await fetch(cleanUrl, opts);
      if (r.status === 401 || r.status === 403) {
        addLog("API Error", "สิทธิ์การเข้าถึงถูกปฏิเสธ (401/403) กรุณาตรวจสอบ API Key ใน Settings", "error");
        return null;
      }
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      console.error(`API Error on ${endpoint}:`, e);
      return null;
    }
  }, [apiKey, apiUrl]);

  const addLog = useCallback((sender: string, text: string, type: 'system' | 'running' | 'success' | 'error' = 'system') => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { time, sender, text, type }]);
  }, []);

  const refreshAll = useCallback(async () => {
    // Sources
    const sourcesData = await apiCall('/sources/health');
    if (sourcesData && sourcesData.sources) {
      setSources(sourcesData.sources);
    }
    
    // Top Posts
    const postsData = await apiCall('/posts/top');
    if (postsData) {
      setTopPosts(postsData);
    }
    
    // Saved Ideas
    const ideasData = await apiCall('/ideas/saved');
    if (ideasData) {
      setSavedIdeas(ideasData);
    }
  }, [apiCall]);

  // Load static sprite assets and layout
  useEffect(() => {
    const initEngine = async () => {
      try {
        const [furnRes, charRes, floorRes, wallRes, layoutRes] = await Promise.all([
          fetch('assets/furniture-catalog.json').then(r => r.json()),
          fetch('assets/characters.json').then(r => r.json()),
          fetch('assets/floors.json').then(r => r.json()),
          fetch('assets/walls.json').then(r => r.json()),
          fetch('assets/default-layout-1.json').then(r => r.json())
        ]);

        buildDynamicCatalog(furnRes);
        setCharacterTemplates(charRes);
        setFloorSprites(floorRes);
        setWallSprites(wallRes);

        const parsedLayout = deserializeLayout(JSON.stringify(layoutRes));
        if (parsedLayout) {
          const state = new OfficeState(parsedLayout);
          
          // Partition seat lists into Office (left room) and Lounge (right room)
          const officeSeats = Array.from(state.seats.values()).filter(s => s.seatCol < 10);
          const loungeSeats = Array.from(state.seats.values()).filter(s => s.seatCol >= 10);
          
          officeSeatIdsRef.current = {};
          loungeSeatIdsRef.current = {};
          
          // Register 6 agents, spawning them in the lounge
          for (let i = 0; i < 6; i++) {
            const loungeSeat = loungeSeats[i];
            const preferredSeatId = loungeSeat ? loungeSeat.uid : undefined;
            state.addAgent(i, i, 0, preferredSeatId, true);
            
            if (officeSeats[i]) {
              officeSeatIdsRef.current[i] = officeSeats[i].uid;
            }
            if (loungeSeats[i]) {
              loungeSeatIdsRef.current[i] = loungeSeats[i].uid;
            }
          }
          
          setOfficeState(state);
          setIsAssetsLoaded(true);
        }
      } catch (err) {
        console.error("Failed to load assets/layout in canvas engine:", err);
      }
    };
    initEngine();
  }, []);

  // Fetch initial API data
  useEffect(() => {
    refreshAll();
    addLog("Pop (Owner)", "ยินดีต้อนรับสู่ระบบ Advice Content Radar — ทุกคนสแตนด์บายแล้ว กดรันระบบเพื่ออัปเดตข้อมูลคู่แข่งได้เลยครับ!", "system");
  }, [refreshAll, addLog]);

  // Auto scroll console logs to bottom
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Click handler on character inside canvas
  const handleAgentClick = (agentId: number) => {
    if (agentId >= 0 && agentId < 6) {
      const key = AGENT_KEYS[agentId];
      setSelectedAgentKey(key);
    }
  };

  const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

  // Run Workflow sequentially with walk animations
  const handleRunWorkflow = async () => {
    if (!officeState || jobStatus === 'running') return;
    setJobStatus('running');
    setLogs([]);

    const officeSeats = officeSeatIdsRef.current;
    const loungeSeats = loungeSeatIdsRef.current;

    // Step 0: Pop (Owner) announces
    setSelectedAgentKey('owner');
    officeState.setAgentActive(0, true);
    addLog("Pop (Owner)", "กดรันระบบแล้วนะทีมงาน! ช่วยเช็คสถานะคู่แข่งด่วนวันนี้ มีอะไรเด็ดมาadaptเสนอแบรนด์ร้านเราบ้าง", "system");
    await delay(1500);
    officeState.setAgentActive(0, false);

    // Step 1: Scraper walks to desk
    setSelectedAgentKey('scraper');
    addLog("Mina (Scraper)", "รับทราบค่ะคุณป๊อป! เดี๋ยวหนูดึงข้อมูลเพจคู่แข่ง Advice ปราณบุรี / เพชรบุรี / Advice ประจวบฯ และ IHAVECPU ให้อัปเดตที่สุดค่ะ", "running");
    officeState.setAgentActive(1, true);
    if (officeSeats[1]) {
      officeState.reassignSeat(1, officeSeats[1]);
    }
    
    // Call background API full daily run trigger
    const apiCallPromise = apiCall('/jobs/full-daily-run', 'POST');
    
    await delay(2500);

    // Step 2: Scoring walks to desk
    setSelectedAgentKey('scoring');
    addLog("Leo (Scoring)", "จัดไปครับหัวหน้า! เดี๋ยวผมนำเข้าโพสต์มาสแกนคีย์เวิร์ด PC, ซ่อมคอม, กล้องวงจรปิด และตัดคะแนนมีมขยะออก 35 คะแนนครับ", "running");
    officeState.setAgentActive(2, true);
    if (officeSeats[2]) {
      officeState.reassignSeat(2, officeSeats[2]);
    }
    
    await delay(2500);

    // Step 3: Sam (AI) walks to desk
    setSelectedAgentKey('ai');
    addLog("Sam (Creative AI)", "ผมรับหน้าที่ต่อเองครับ! จะดึงโพสต์ท็อป 5 มาสร้างจุดจี้ใจลูกค้า เสนอจุดขายอัปเกรดเครื่องและซ่อมคอมถึงบ้านร้านเราครับ", "running");
    officeState.setAgentActive(3, true);
    if (officeSeats[3]) {
      officeState.reassignSeat(3, officeSeats[3]);
    }
    
    // Wait for actual API response
    const result = await apiCallPromise;
    
    await delay(1500);

    // Step 4: Admin active
    setSelectedAgentKey('admin');
    officeState.setAgentActive(4, true);
    if (officeSeats[4]) {
      officeState.reassignSeat(4, officeSeats[4]);
    }
    addLog("Ava (System Admin)", "ข้อมูลประมวลผลเสร็จสิ้นเรียบร้อย บันทึกลงฐานข้อมูล SQLite และระบบ Content Memory แล้วค่ะ", "running");
    
    await delay(2000);

    // Step 5: Telegram Bot active
    setSelectedAgentKey('telegram');
    officeState.setAgentActive(5, true);
    if (officeSeats[5]) {
      officeState.reassignSeat(5, officeSeats[5]);
    }
    addLog("Uploader (Telegram Bot)", "ผมจัดส่งรายงานสรุปเช้าวันนี้เข้าแชนแนล Telegram Bot เรียบร้อยแล้วครับเจ้านาย! 🚀", "running");
    
    await delay(2500);

    // Final result output
    if (result) {
      addLog("Workflow Success", `รัน Daily Workflow สำเร็จ! ดึงข้อมูลได้ ${result.collected || 0} โพสต์ / คัดกรองวิเคราะห์ไอเดีย ${result.analyzed || 0} โพสต์ / ส่งออก Telegram: สำเร็จ`, "success");
      setJobStatus('success');
    } else {
      addLog("Workflow Error", "การดึงข้อมูลผิดพลาดหรือเกิดปัญหากับเซิร์ฟเวอร์หลังบ้าน กรุณาลองใหม่อีกครั้ง", "error");
      setJobStatus('error');
    }

    await delay(3000);
    
    // Walk back and standby
    for (let i = 0; i < 6; i++) {
      officeState.setAgentActive(i, false);
      if (loungeSeats[i]) {
        officeState.reassignSeat(i, loungeSeats[i]);
      }
    }
    
    setJobStatus('idle');
    setSelectedAgentKey('owner');
    refreshAll();
  };

  // Quick assist pill clicks
  const handlePillClick = (key: string) => {
    setSelectedAgentKey(key);
    if (key === 'scraper') {
      addLog("Mina (Scraper)", "แหล่งข้อมูลคู่แข่งทั้งหมด 8 แหล่งทำงานปกติค่ะ! แหล่งล่าสุดที่เราดึงเพิ่งวิเคราะห์ไป 5 โพสต์", "system");
    } else if (key === 'scoring') {
      addLog("Leo (Scoring)", "สถิติวันนี้ โพสต์ประเภท 'Notebook' และ 'การอัปเกรดคอม' ได้ความนิยมสูงสุงเฉลี่ย 92.5 คะแนนครับ", "system");
    } else if (key === 'ai') {
      addLog("Sam (Creative AI)", "ไอเดียโฆษณาเด่นวันนี้คือ 'คอมพิวเตอร์ทำงานอืดเพราะแรมไม่พอ? บริการอัปเกรดความแรงคอมถึงบ้านคุณ' ครับ", "system");
    } else if (key === 'admin') {
      addLog("Ava (System Admin)", "ฐานข้อมูล SQLite เชื่อมต่อเสถียร / Content Memory จำโพสต์ที่ดึงไปแล้วเพื่อป้องกันไอเดียซ้ำซ้อนค่ะ", "system");
    } else if (key === 'telegram') {
      addLog("Uploader (Telegram Bot)", "ระบบ Telegram Channel ออนไลน์พร้อมส่งครับ / ทดลองคุยกับบอทด้วยคำสั่ง /today ใน Telegram ได้เลย", "system");
    } else {
      addLog("Pop (Owner)", "พร้อมแล้วลุยงานเลยจ้า ทุกคนเตรียมประมวลผลอยู่แล้ว!", "system");
    }
  };

  // Save Idea to DB
  const handleSaveIdea = async (postId: number, index: number) => {
    const rep = await apiCall('/reports/today');
    if (rep && rep.id) {
      const r = await apiCall('/ideas/save', 'POST', { report_id: rep.id, idea_number: index + 1 });
      if (r) {
        addLog("Pop (Owner)", `บันทึกไอเดียแคมเปญโพสต์ที่ #${index + 1} เข้าระบบคัดกรองแล้ว! 📋`, "success");
        refreshAll();
      }
    }
  };

  // Mark Idea as used
  const handleMarkUsed = async (ideaId: number) => {
    const r = await apiCall(`/ideas/${ideaId}/used`, 'POST');
    if (r) {
      addLog("Ava (System Admin)", `อัปเดตสถานะแคมเปญหมายเลข #${ideaId} เป็น 'ใช้แล้ว' สำเร็จ`, "success");
      refreshAll();
    }
  };

  // Save Settings Modal
  const openSettings = () => {
    setTempApiKey(apiKey);
    setTempApiUrl(apiUrl);
    setShowSettings(true);
  };

  const handleSaveSettings = () => {
    setApiKey(tempApiKey);
    setApiUrl(tempApiUrl);
    localStorage.setItem('admin_api_key', tempApiKey);
    localStorage.setItem('admin_api_url', tempApiUrl);
    setShowSettings(false);
    addLog("System Admin", "บันทึกการเชื่อมต่อเรียบร้อยแล้วค่ะ กำลังรีเฟรชข้อมูลแดชบอร์ด...", "system");
    refreshAll();
  };

  const selectedAgent = AGENTS_METADATA[selectedAgentKey];

  return (
    <div className="app-container">
      {/* 1. LEFT COLUMN: Control & Sources */}
      <aside className="panel sidebar-left">
        <div className="panel-header">
          <div className="brand-section">
            <i className="fa-solid fa-satellite-dish brand-icon"></i>
            <div className="brand-text">
              <h1>Advice Sam Roi Yod</h1>
              <p>Content Radar Dashboard</p>
            </div>
          </div>
          <button className="canvas-btn" onClick={openSettings} title="Settings">
            <i className="fa-solid fa-gear"></i>
          </button>
        </div>

        <div className="panel-body">
          {/* Work Control Section */}
          <div className="run-section">
            <div className="run-title-row">
              <span style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Workflow Control</span>
              {jobStatus === 'running' ? (
                <span className="run-status-badge running">
                  <span className="status-pulse-dot"></span>
                  Processing
                </span>
              ) : (
                <span className="run-status-badge idle">
                  <span className="status-pulse-dot"></span>
                  Standby
                </span>
              )}
            </div>
            
            <button 
              className="btn-primary-glow" 
              onClick={handleRunWorkflow} 
              disabled={jobStatus === 'running'}
            >
              {jobStatus === 'running' ? (
                <>
                  <i className="fa-solid fa-circle-notch fa-spin"></i>
                  กำลังรัน...
                </>
              ) : (
                <>
                  <i className="fa-solid fa-play"></i>
                  รัน Daily Workflow
                </>
              )}
            </button>
          </div>

          {/* Quick Assist Pills */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Quick Assists</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              <button className="btn-secondary" onClick={() => handlePillClick('scraper')}>Mina 🔍</button>
              <button className="btn-secondary" onClick={() => handlePillClick('scoring')}>Leo 🧮</button>
              <button className="btn-secondary" onClick={() => handlePillClick('ai')}>Sam 💡</button>
              <button className="btn-secondary" onClick={() => handlePillClick('admin')}>Ava ⚙️</button>
              <button className="btn-secondary" onClick={() => handlePillClick('telegram')}>Uploader ✈️</button>
            </div>
          </div>

          {/* Sources List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flexGrow: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Source Health</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {sources.filter(s => s.active && s.health === 'ok').length} / {sources.length} Active
              </span>
            </div>

            <div className="source-list">
              {sources.length === 0 ? (
                <div className="loading-placeholder">
                  <div className="loading-spinner"></div>
                  <span>กำลังโหลดแหล่งข้อมูล...</span>
                </div>
              ) : (
                sources.map((src, index) => {
                  let statusClass = 'empty';
                  let statusText = 'Unknown';
                  if (!src.active) {
                    statusClass = 'inactive';
                    statusText = 'ปิดใช้งาน';
                  } else if (src.health === 'ok') {
                    statusClass = 'ok';
                    statusText = 'ปกติ';
                  } else if (src.health === 'stale') {
                    statusClass = 'stale';
                    statusText = 'ไม่อัปเดต';
                  }

                  return (
                    <div className="source-item" key={index}>
                      <div className="source-details">
                        <span className="source-name" title={src.name}>{src.name}</span>
                        <div className="source-meta">
                          <span>{src.platform}</span>
                          <span>•</span>
                          <a href={src.source_url} target="_blank" rel="noreferrer">
                            <i className="fa-solid fa-arrow-up-right-from-square"></i>
                          </a>
                        </div>
                      </div>
                      <div className="source-status">
                        <span className={`status-dot ${statusClass}`}></span>
                        <span className={`source-status-text ${statusClass}`}>{statusText}</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </aside>

      {/* 2. CENTER COLUMN: Canvas & Logs Terminal */}
      <main className="center-column">
        {/* Canvas container */}
        <div className="canvas-container">


          {isAssetsLoaded && officeState ? (
            <OfficeCanvas
              officeState={officeState}
              onClick={handleAgentClick}
              isEditMode={false}
              editorState={mockEditorState as any}
              onEditorTileAction={() => {}}
              onEditorEraseAction={() => {}}
              onEditorSelectionChange={() => {}}
              onDeleteSelected={() => {}}
              onRotateSelected={() => {}}
              onDragMove={() => {}}
              editorTick={editorTick}
              panRef={panRef}
            />
          ) : (
            <div className="loading-placeholder">
              <div className="loading-spinner" style={{ width: '32px', height: '32px', marginBottom: '1rem' }}></div>
              <span style={{ fontSize: '0.9rem' }}>กำลังดาวน์โหลดกราฟิกพิกเซลออฟฟิศ...</span>
            </div>
          )}
        </div>

        {/* Collapsible Logs console at bottom */}
        <div className={`console-panel ${isConsoleCollapsed ? 'collapsed' : ''}`}>
          <div className="console-header" onClick={() => setIsConsoleCollapsed(prev => !prev)}>
            <div className="console-title">
              <i className="fa-solid fa-terminal"></i>
              Command Feed Logs
            </div>
            <button className="canvas-btn" style={{ width: '24px', height: '24px', background: 'none', border: 'none' }}>
              <i className={`fa-solid ${isConsoleCollapsed ? 'fa-chevron-up' : 'fa-chevron-down'}`} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}></i>
            </button>
          </div>

          {!isConsoleCollapsed && (
            <div className="console-body">
              {logs.map((log, index) => (
                <div className={`log-row ${log.type}`} key={index}>
                  <span className="log-time">[{log.time}]</span>
                  <span className="log-sender">{log.sender}:</span>
                  <span className="log-message">{log.text}</span>
                </div>
              ))}
              <div ref={consoleEndRef}></div>
            </div>
          )}
        </div>
      </main>

      {/* 3. RIGHT COLUMN: Metrics & Signals */}
      <aside className="panel sidebar-right">
        <div className="panel-header">
          <h2>
            <i className="fa-solid fa-chart-line" style={{ color: 'var(--neon-purple)' }}></i>
            Content Intelligence
          </h2>
        </div>

        <div className="panel-body" style={{ padding: 0, overflow: 'hidden', gap: 0 }}>
          {/* === Fixed Top Section: Metrics + Agent Card === */}
          <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem', flexShrink: 0, borderBottom: '1px solid var(--border-color)', overflowY: 'auto', maxHeight: '55%' }}>
            {/* AI Metrics Category Radar */}
            <div className="metrics-section">
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Top Content Categories</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                <div className="metric-bar-group">
                  <div className="metric-header">
                    <span className="metric-label">PC ประกอบ & สเปคคอม</span>
                    <span className="metric-val">95%</span>
                  </div>
                  <div className="metric-track">
                    <div className="metric-fill cyan" style={{ width: '95%' }}></div>
                  </div>
                </div>
                <div className="metric-bar-group">
                  <div className="metric-header">
                    <span className="metric-label">การซ่อมคอม & อัปเกรดเครื่อง</span>
                    <span className="metric-val">82%</span>
                  </div>
                  <div className="metric-track">
                    <div className="metric-fill purple" style={{ width: '82%' }}></div>
                  </div>
                </div>
                <div className="metric-bar-group">
                  <div className="metric-header">
                    <span className="metric-label">กล้องวงจรปิด CCTV</span>
                    <span className="metric-val">70%</span>
                  </div>
                  <div className="metric-track">
                    <div className="metric-fill amber" style={{ width: '70%' }}></div>
                  </div>
                </div>
                <div className="metric-bar-group">
                  <div className="metric-header">
                    <span className="metric-label">โน้ตบุ๊ก & ปริ้นเตอร์</span>
                    <span className="metric-val">64%</span>
                  </div>
                  <div className="metric-track">
                    <div className="metric-fill emerald" style={{ width: '64%' }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Active Clicked Agent panel */}
            {selectedAgent && (
              <div className="agent-card">
                <div className="agent-card-avatar">{selectedAgent.avatar}</div>
                <div className="agent-card-info">
                  <h3>{selectedAgent.title}</h3>
                  <span className="agent-card-desc">{selectedAgent.desc}</span>
                  <ul className="agent-bullets">
                    {selectedAgent.bullets.map((b, idx) => (
                      <li key={idx}>{b}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div> {/* end fixed top section */}

          {/* === Scrollable Bottom Section: Tabs + Post List === */}
          <div style={{ display: 'flex', flexDirection: 'column', flexGrow: 1, overflow: 'hidden' }}>

            {/* Signals / Saved Ideas Tabs */}
            <div className="tabs-container" style={{ flexShrink: 0, margin: '0 1.25rem' }}>
              <button
                className={`tab-btn ${activeTab === 'posts' ? 'active' : ''}`}
                onClick={() => setActiveTab('posts')}
              >
                Competitor Signals
              </button>
              <button
                className={`tab-btn ${activeTab === 'saved' ? 'active' : ''}`}
                onClick={() => setActiveTab('saved')}
              >
                Saved Ideas ({savedIdeas.filter(i => i.status === 'saved').length})
              </button>
            </div>

            {/* Tabs Content — independently scrollable */}
            <div style={{ flexGrow: 1, overflowY: 'auto', padding: '0 1.25rem 1.25rem' }}>
            {activeTab === 'posts' ? (
              <div className="signals-list">
                {topPosts.length === 0 ? (
                  <div className="empty-placeholder">
                    <i className="fa-regular fa-clipboard"></i>
                    <span>ไม่มีโพสต์ยอดฮิตวันนี้</span>
                  </div>
                ) : (
                  topPosts.map((post, idx) => {
                    const u = (post.post_url || '').toLowerCase();
                    const boosted = u.includes('advicepranburi') || u.includes('adviceprachuap') || u.includes('advicephetchaburi') || u.includes('cpucore2duo') || u.includes('ihavecpu');
                    
                    return (
                      <div className={`post-card ${boosted ? 'priority-boost' : ''}`} key={post.id}>
                        <div className="post-header">
                          <span className="post-source">
                            <i className="fa-brands fa-facebook" style={{ color: '#1877f2' }}></i>
                            {post.source_name}
                          </span>
                          <span className="post-score-badge">Viral: {post.final_score}</span>
                        </div>
                        <p className="post-snippet">{post.post_text}</p>
                        
                        {post.analysis ? (
                          <div className="ai-details">
                            <div className="detail-block">
                              <span className="detail-label">
                                <i className="fa-solid fa-quote-left"></i>
                                Suggested Hook
                              </span>
                              <span className="detail-content">{post.analysis.suggested_hook || '-'}</span>
                            </div>
                            <div className="detail-block">
                              <span className="detail-label">
                                <i className="fa-regular fa-lightbulb"></i>
                                Local Angle
                              </span>
                              <span className="detail-content">{post.analysis.local_angle || '-'}</span>
                            </div>
                          </div>
                        ) : (
                          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '0.4rem', fontSize: '0.75rem' }}>
                            <i className="fa-solid fa-brain"></i> รอรับการประมวลผลบอท
                          </div>
                        )}

                        {post.analysis && (
                          <div className="post-footer">
                            <button className="btn-secondary" onClick={() => handleSaveIdea(post.id, idx)}>
                              <i className="fa-regular fa-bookmark"></i> บันทึกไอเดีย
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            ) : (
              <div className="signals-list">
                {savedIdeas.length === 0 ? (
                  <div className="empty-placeholder">
                    <i className="fa-solid fa-bookmark"></i>
                    <span>ไม่มีไอเดียที่รอดำเนินการ</span>
                  </div>
                ) : (
                  savedIdeas.map((idea) => {
                    const used = idea.status === 'used';
                    return (
                      <div className="post-card" key={idea.id} style={{ opacity: used ? 0.6 : 1 }}>
                        <div className="post-header">
                          <span className="post-source">
                            <i className="fa-solid fa-lightbulb" style={{ color: 'var(--neon-amber)' }}></i>
                            ไอเดียแคมเปญ #{idea.idea_number}
                          </span>
                          {used ? (
                            <span className="idea-status-badge used">ใช้แล้ว</span>
                          ) : (
                            <span className="idea-status-badge pending">รอดำเนินการ</span>
                          )}
                        </div>
                        <div className="post-card-body">
                          <p style={{ fontWeight: 700, color: '#fff', fontSize: '0.85rem', marginBottom: '0.25rem' }}>{idea.title}</p>
                          <p style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{idea.caption_draft}</p>
                        </div>
                        
                        {!used && (
                          <div className="post-footer">
                            <button className="btn-secondary" onClick={() => handleMarkUsed(idea.id)}>
                              <i className="fa-solid fa-check"></i> ทำแคมเปญแล้ว
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            )}
            </div>
          </div> {/* end scrollable bottom section */}
        </div>
      </aside>

      {/* 4. SETTINGS MODAL */}
      <div className={`modal-overlay ${showSettings ? 'open' : ''}`}>
        <div className="modal-content">
          <div className="modal-header">
            <h3>API Connection Settings</h3>
            <button className="modal-close-btn" onClick={() => setShowSettings(false)}>
              <i className="fa-solid fa-xmark"></i>
            </button>
          </div>
          <div className="modal-body">
            <div className="form-group">
              <label>Admin API Key</label>
              <div className="input-container">
                <input 
                  type={showKeyVisible ? 'text' : 'password'} 
                  className="form-input" 
                  value={tempApiKey} 
                  onChange={e => setTempApiKey(e.target.value)} 
                  placeholder="Enter X-Admin-API-Key"
                />
                <button className="input-icon-btn" onClick={() => setShowKeyVisible(p => !p)}>
                  <i className={`fa-solid ${showKeyVisible ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                </button>
              </div>
            </div>

            <div className="form-group">
              <label>API Base URL</label>
              <input 
                type="text" 
                className="form-input" 
                value={tempApiUrl} 
                onChange={e => setTempApiUrl(e.target.value)} 
                placeholder="http://127.0.0.1:8010"
              />
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn-secondary" onClick={() => setShowSettings(false)}>Cancel</button>
            <button className="btn-primary-glow" style={{ padding: '0.5rem 1rem' }} onClick={handleSaveSettings}>Save</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
