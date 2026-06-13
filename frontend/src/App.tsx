import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';

import './App.css';
import { OfficeCanvas } from './office/components/OfficeCanvas.js';
import { OfficeState } from './office/engine/officeState.js';
import { deserializeLayout } from './office/layout/layoutSerializer.js';
import { buildDynamicCatalog } from './office/layout/furnitureCatalog.js';
import { setCharacterTemplates } from './office/sprites/spriteData.js';
import { setFloorSprites } from './office/floorTiles.js';
import { setWallSprites } from './office/wallTiles.js';
import type { EditorState } from './office/editor/editorState.js';
import type { OpsSummary, SourceHealthItem } from './types/ops.js';

type ActionState = 'idle' | 'running' | 'success' | 'error';
type BannerTone = 'idle' | 'running' | 'success' | 'warning' | 'error';

interface ActionConfig {
  key: string;
  label: string;
  endpoint: string;
  phase: string;
  description: string;
  primary?: boolean;
}

interface ActivityEntry {
  id: number;
  time: string;
  title: string;
  detail: string;
  tone: BannerTone;
}

interface ApiResult<T> {
  data: T | null;
  error: string | null;
}

interface ActionOutcome {
  state: ActionState;
  tone: BannerTone;
  title: string;
  detail: string;
}

const AGENTS = [
  { id: 0, key: 'pop', name: 'คุณป๊อป เจ้าของร้าน' },
  { id: 1, key: 'mina', name: 'มีนา เก็บข้อมูล' },
  { id: 2, key: 'leo', name: 'ลีโอ จัดอันดับ' },
  { id: 3, key: 'sam', name: 'แซม AI คอนเทนต์' },
  { id: 4, key: 'ava', name: 'เอวา ทำรายงาน' },
  { id: 5, key: 'uploader', name: 'ส่งเข้า Telegram' },
];

const PRIMARY_ACTIONS: ActionConfig[] = [
  {
    key: 'full-daily-run',
    label: 'รันระบบเต็มรูปแบบ',
    endpoint: '/jobs/full-daily-run?send=true',
    phase: 'กำลังเก็บข้อมูล วิเคราะห์ สร้างรายงาน และส่ง Telegram',
    description: 'ทำ workflow รายวันครบทุกขั้นตอน',
    primary: true,
  },
  {
    key: 'send-telegram',
    label: 'ส่ง Telegram',
    endpoint: '/reports/send-telegram',
    phase: 'กำลังส่งรายงานล่าสุดเข้า Telegram',
    description: 'ใช้รายงานล่าสุดที่มีอยู่แล้ว',
  },
  {
    key: 'refresh',
    label: 'รีเฟรชสถานะ',
    endpoint: '',
    phase: 'กำลังโหลดสถานะล่าสุด',
    description: 'อัปเดตตัวเลขและสถานะบน Dashboard',
  },
];

const MORE_ACTIONS: ActionConfig[] = [
  { key: 'collect', label: 'เก็บข้อมูล', endpoint: '/jobs/collect', phase: 'กำลังดึงข้อมูลจากแหล่งที่ตั้งไว้', description: 'ดึงโพสต์ใหม่จาก source' },
  { key: 'score', label: 'คำนวณคะแนน', endpoint: '/jobs/score', phase: 'กำลังจัดอันดับโพสต์ที่เก็บมา', description: 'คำนวณ viral และ local relevance' },
  { key: 'analyze', label: 'วิเคราะห์ด้วย AI', endpoint: '/jobs/analyze', phase: 'กำลังให้ AI วิเคราะห์โพสต์เด่น', description: 'สร้าง insight และมุมคอนเทนต์' },
  { key: 'generate-report', label: 'สร้างรายงาน', endpoint: '/reports/generate', phase: 'กำลังประกอบรายงานประจำวัน', description: 'รวม brief สำหรับร้าน' },
];

const STATUS_LABELS: Record<string, string> = {
  ok: 'ปกติ',
  running: 'กำลังทำงาน',
  stale: 'ข้อมูลเก่า',
  error: 'ผิดพลาด',
  none: 'ยังไม่เคยรัน',
  missing: 'ยังไม่มีข้อมูล',
  outdated: 'ล้าสมัย',
  too_long: 'ข้อความยาวเกิน',
  sent: 'ส่งแล้ว',
  not_sent: 'ยังไม่ส่ง',
  no_report: 'ยังไม่มีรายงาน',
  empty: 'ไม่มีข้อมูล',
  inactive: 'ปิดใช้งาน',
  saved: 'บันทึกแล้ว',
  used: 'ใช้แล้ว',
  warning: 'ต้องตรวจ',
  info: 'แจ้งทราบ',
};

const PRODUCTION_LABELS: Record<string, string> = {
  ADMIN_API_KEY: 'ตั้งค่า ADMIN_API_KEY',
  'ADMIN_API_KEY configured': 'ตั้งค่า ADMIN_API_KEY',
  TELEGRAM_WEBHOOK_SECRET: 'ตั้งค่า TELEGRAM_WEBHOOK_SECRET',
  'TELEGRAM_WEBHOOK_SECRET configured': 'ตั้งค่า TELEGRAM_WEBHOOK_SECRET',
  ALLOWED_TELEGRAM_CHAT_IDS: 'ตั้งค่า ALLOWED_TELEGRAM_CHAT_IDS',
  'ALLOWED_TELEGRAM_CHAT_IDS configured': 'ตั้งค่า ALLOWED_TELEGRAM_CHAT_IDS',
  'Telegram token/chat id configured': 'ตั้งค่า Telegram token/chat id',
  'Database URL configured': 'ตั้งค่า Database URL',
};

const EMPTY_SUMMARY: OpsSummary = {
  latest_job: { status: 'none', name: null, started_at: null, finished_at: null, error: null },
  sources: { total: 0, ok: 0, empty: 0, stale: 0, inactive: 0, items: [] },
  report: { status: 'missing', report_date: null, message_length: 0, top_posts_count: 0 },
  telegram: { status: 'no_report', sent_at: null },
  saved_ideas: { total: 0, saved: 0, used: 0, items: [] },
  production: { checks: [] },
  top_issues: [],
};

const ACTION_AGENT_IDS: Record<string, number[]> = {
  'full-daily-run': [1, 2, 3, 4, 5],
  collect: [1],
  score: [2],
  analyze: [3],
  'generate-report': [4],
  'send-telegram': [5],
  refresh: [0],
};

const STANDBY_TILES = [
  { col: 14, row: 18 },
  { col: 15, row: 18 },
  { col: 16, row: 18 },
  { col: 13, row: 18 },
  { col: 17, row: 18 },
  { col: 10, row: 18 },
];

const AGENTS_METADATA: Record<number, {
  id: number;
  avatar: string;
  title: string;
  role: string;
  desc: string;
  bullets: string[];
}> = {
  0: {
    id: 0,
    avatar: '🕵️',
    title: 'คุณป๊อป (Pop)',
    role: 'Shop Operator / เจ้าของร้าน',
    desc: 'ผู้ควบคุมดูแลทิศทางการตลาดและมีสิทธิ์อนุมัติแคมเปญสุดท้ายของร้าน Advice สามร้อยยอด',
    bullets: [
      'ตัดสินใจเลือกแนวคิดแคมเปญที่เหมาะสมที่สุด',
      'ควบคุมและปรับแต่งทิศทางการตลาดของร้าน',
      'ตรวจรับและอนุมัติเนื้อหาโพสต์ลงเพจเฟสบุ๊คหลัก'
    ]
  },
  1: {
    id: 1,
    avatar: '🔍',
    title: 'มีนา (Mina)',
    role: 'Spy Scraper / ฝ่ายเก็บข้อมูลคู่แข่ง',
    desc: 'ผู้ดูแลบอทดึงข้อมูลโพสต์และยอด engagement จากเพจคู่แข่ง Advice สาขาอื่น และเพจ IT ชั้นนำ',
    bullets: [
      'ตรวจสอบโพสต์ของสาขา ปราณบุรี / เพชรบุรี / ประจวบฯ',
      'สืบค้นข้อมูลเทรนด์จากเว็บข่าวและเพจไอทีชั้นนำ',
      'คัดกรองเฉพาะหัวข้อที่เกี่ยวกับคอมพิวเตอร์และงานซ่อม'
    ]
  },
  2: {
    id: 2,
    avatar: '🧮',
    title: 'ลีโอ (Leo)',
    role: 'Score Engine / ฝ่ายจัดอันดับและวิเคราะห์คะแนน',
    desc: 'ผู้คำนวณ Viral Score ประเมินความสนใจของโพสต์ คัดแยกระหว่างเทรนด์แท้และมีมทั่วไป',
    bullets: [
      'คำนวณน้ำหนักการมีส่วนร่วม (Like / Share / Comment)',
      'ตัดคะแนนมีมทั่วไป หรือข่าวที่ไม่ก่อให้เกิดยอดซ่อม/ซื้อเครื่อง',
      'เพิ่มคะแนน (Boost) ให้กับสาขาใกล้เคียงและหมวดสินค้าขายดี'
    ]
  },
  3: {
    id: 3,
    avatar: '💡',
    title: 'แซม (Sam)',
    role: 'Creative AI / ฝ่ายเขียนคอนเทนต์สร้างสรรค์',
    desc: 'ระบบ AI คิดมุมโปรโมชันและแปลกใหม่ที่เข้ากับจุดขายของร้าน Advice สามร้อยยอด',
    bullets: [
      'วิเคราะห์จุดจี้ใจ (Pain Point) และความต้องการของลูกค้า',
      'เชื่อมโยงคอนเทนต์กับบริการของร้าน เช่น ซ่อมคอมถึงบ้าน',
      'เขียนสคริปต์วิดีโอสั้น (Reels) และดราฟต์แคปชันภาษาไทย'
    ]
  },
  4: {
    id: 4,
    avatar: '⚙️',
    title: 'เอวา (Ava)',
    role: 'System Admin / ผู้ดูแลฐานข้อมูลรายงาน',
    desc: 'ผู้ดูแลระบบฐานข้อมูล SQLite/PostgreSQL และบันทึกประวัติการวิเคราะห์ย้อนหลัง (Content Memory)',
    bullets: [
      'จัดการ API Key และตรวจสอบการทำงานของหลังบ้าน',
      'ป้องกันความปลอดภัย ตรวจสอบช่องโหว่ประเภท SSRF',
      'ควบคุมไม่ให้ระบบสร้างหัวข้อคอนเทนต์ซ้ำกับช่วง 14 วันล่าสุด'
    ]
  },
  5: {
    id: 5,
    avatar: '✈️',
    title: 'Uploader (Telegram Bot)',
    role: 'Telegram Bot / ผู้ส่งรายงานและคำสั่งระบบ',
    desc: 'บอทผู้รับหน้าที่จัดส่งสรุปบรีฟการตลาดเข้าระบบ Telegram Bot ทุกเช้าเวลา 06:00 น.',
    bullets: [
      'จัดแบ่งรูปแบบบรีฟคอนเทนต์ตามเกณฑ์ความยาว 4096 ตัวอักษร',
      'มีระบบส่งซ้ำ (Retry) อัตโนมัติสูงสุด 3 ครั้งเพื่อป้องกันระบบล่ม',
      'รองรับการตอบกลับด้วยคำสั่งพิเศษ เช่น /caption, /reels, /carousel'
    ]
  }
};

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
  clearSelection: () => {},
} as unknown as EditorState;

function App() {
  const [summary, setSummary] = useState<OpsSummary>(EMPTY_SUMMARY);
  const [isLoading, setIsLoading] = useState(true);
  const [showMore, setShowMore] = useState(false);
  const [apiKey, setApiKey] = useState(() => getStoredSetting('admin_api_key', ''));
  const [apiUrl, setApiUrl] = useState(() => getStoredSetting('admin_api_url', window.location.origin));
  const [tempApiKey, setTempApiKey] = useState('');
  const [tempApiUrl, setTempApiUrl] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [officeState, setOfficeState] = useState<OfficeState | null>(null);
  const [isAssetsLoaded, setIsAssetsLoaded] = useState(false);
  const [activeAction, setActiveAction] = useState<ActionConfig | null>(null);
  const [actionStates, setActionStates] = useState<Record<string, ActionState>>({});
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [banner, setBanner] = useState<{ tone: BannerTone; title: string; detail: string }>({
    tone: 'idle',
    title: 'พร้อมรับคำสั่ง',
    detail: 'เลือกคำสั่งด้านซ้าย ระบบจะแสดงสถานะทันทีเมื่อเริ่มทำงาน',
  });
  const [activityLog, setActivityLog] = useState<ActivityEntry[]>(() => [
    {
      id: Date.now(),
      time: formatTime(),
      title: 'Dashboard พร้อมใช้งาน',
      detail: 'รอคำสั่งจากผู้ดูแล',
      tone: 'idle',
    },
  ]);
  const [editorTick] = useState(0);
  const panRef = useRef({ x: 0, y: 0 });

  const setActionState = useCallback((key: string, state: ActionState) => {
    setActionStates((current) => ({ ...current, [key]: state }));
  }, []);

  const addActivity = useCallback((title: string, detail: string, tone: BannerTone) => {
    setActivityLog((current) => [
      { id: Date.now() + Math.random(), time: formatTime(), title, detail, tone },
      ...current,
    ].slice(0, 7));
  }, []);

  const apiRequest = useCallback(
    async <T,>(endpoint: string, method = 'GET', body?: object): Promise<ApiResult<T>> => {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (apiKey) headers['X-Admin-API-Key'] = apiKey;

      try {
        const response = await fetch(`${apiUrl.replace(/\/$/, '')}${endpoint}`, {
          method,
          headers,
          body: body ? JSON.stringify(body) : undefined,
        });
        if (!response.ok) {
          return { data: null, error: apiErrorMessage(response.status) };
        }
        return { data: (await response.json()) as T, error: null };
      } catch (err) {
        return { data: null, error: err instanceof Error ? err.message : 'เรียก API ไม่สำเร็จ' };
      }
    },
    [apiKey, apiUrl],
  );

  const refreshSummary = useCallback(async (silent = false) => {
    if (!silent) setIsLoading(true);
    const result = await apiRequest<OpsSummary>('/ops/summary');
    if (result.data) {
      setSummary(result.data);
    } else if (result.error) {
      setBanner({ tone: 'error', title: 'โหลดสถานะไม่สำเร็จ', detail: result.error });
    }
    if (!silent) setIsLoading(false);
  }, [apiRequest]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshSummary();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [refreshSummary]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      void refreshSummary(true);
    }, 5000);
    return () => window.clearInterval(interval);
  }, [refreshSummary]);

  useEffect(() => {
    const initEngine = async () => {
      try {
        const [furniture, characters, floors, walls, layout] = await Promise.all([
          fetch('assets/furniture-catalog.json').then((r) => r.json()),
          fetch('assets/characters.json').then((r) => r.json()),
          fetch('assets/floors.json').then((r) => r.json()),
          fetch('assets/walls.json').then((r) => r.json()),
          fetch('assets/default-layout-1.json').then((r) => r.json()),
        ]);

        buildDynamicCatalog(furniture);
        setCharacterTemplates(characters);
        setFloorSprites(floors);
        setWallSprites(walls);

        const parsedLayout = deserializeLayout(JSON.stringify(layout));
        if (!parsedLayout) return;

        const state = new OfficeState(parsedLayout);
        const officeSeats = Array.from(state.seats.values()).filter((s) => s.seatCol < 10);
        const loungeSeats = Array.from(state.seats.values()).filter((s) => s.seatCol >= 10);

        for (const agent of AGENTS) {
          let seatUid: string | undefined;
          if (agent.id === 0) {
            seatUid = loungeSeats[0]?.uid;
          } else if (agent.id === 5) {
            seatUid = loungeSeats[1]?.uid;
          } else {
            // agents 1, 2, 3, 4 get office seats 0, 1, 2, 3
            seatUid = officeSeats[agent.id - 1]?.uid;
          }
          state.addAgent(agent.id, agent.id, 0, seatUid, true);
        }
        moveAgentsForAction(state, null);
        setOfficeState(state);
        setIsAssetsLoaded(true);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'โหลดไฟล์ภาพออฟฟิศไม่สำเร็จ';
        setBanner({ tone: 'error', title: 'โหลดฉากออฟฟิศไม่สำเร็จ', detail: message });
        addActivity('โหลดฉากออฟฟิศไม่สำเร็จ', message, 'error');
      }
    };

    void initEngine();
  }, [addActivity]);

  useEffect(() => {
    if (!officeState) return;
    const actionKey = activeAction?.key || (summary.latest_job.status === 'running' ? 'full-daily-run' : null);
    moveAgentsForAction(officeState, actionKey);
  }, [activeAction?.key, officeState, summary.latest_job.status]);

  const requireApiKey = () => {
    return true;
  };

  const runAction = async (action: ActionConfig) => {
    if (action.key !== 'refresh' && !requireApiKey()) return;

    setActiveAction(action);
    setActionState(action.key, 'running');
    setBanner({ tone: 'running', title: action.label, detail: action.phase });
    addActivity(`เริ่ม ${action.label}`, action.phase, 'running');

    const result = action.key === 'refresh'
      ? await apiRequest<OpsSummary>('/ops/summary')
      : await apiRequest<Record<string, unknown>>(action.endpoint, 'POST');

    if (result.data) {
      const outcome = summarizeActionOutcome(action, result.data);
      setActionState(action.key, outcome.state);
      setBanner({ tone: outcome.tone, title: outcome.title, detail: outcome.detail });
      addActivity(outcome.title, outcome.detail, outcome.tone);
      if (action.key === 'refresh') {
        setSummary(result.data as OpsSummary);
      } else {
        await refreshSummary();
      }
    } else {
      const detail = result.error || `${action.label} ไม่สำเร็จ`;
      setActionState(action.key, 'error');
      setBanner({ tone: 'error', title: `${action.label} ไม่สำเร็จ`, detail });
      addActivity(`${action.label} ไม่สำเร็จ`, detail, 'error');
    }

    setActiveAction(null);
  };

  const disableSource = async (source: SourceHealthItem) => {
    if (!window.confirm(`ปิดแหล่งข้อมูล "${source.name}" ใช่ไหม?`)) return;
    if (!requireApiKey()) return;

    const actionKey = `source-${source.source_id}`;
    setActionState(actionKey, 'running');
    setBanner({ tone: 'running', title: 'กำลังปิดแหล่งข้อมูล', detail: source.name });
    const result = await apiRequest<SourceHealthItem>(`/sources/${source.source_id}`, 'PUT', { active: false });
    if (result.data) {
      setActionState(actionKey, 'success');
      addActivity('ปิดแหล่งข้อมูลแล้ว', source.name, 'success');
      await refreshSummary();
    } else {
      setActionState(actionKey, 'error');
      setBanner({ tone: 'error', title: 'ปิดแหล่งข้อมูลไม่สำเร็จ', detail: result.error || source.name });
    }
  };

  const markIdeaUsed = async (ideaId: number) => {
    if (!requireApiKey()) return;

    const actionKey = `idea-${ideaId}`;
    setActionState(actionKey, 'running');
    setBanner({ tone: 'running', title: 'กำลังอัปเดตไอเดีย', detail: `ไอเดีย #${ideaId}` });
    const result = await apiRequest<Record<string, unknown>>(`/ideas/${ideaId}/used`, 'POST');
    if (result.data) {
      setActionState(actionKey, 'success');
      addActivity('ทำเครื่องหมายไอเดียแล้ว', `ไอเดีย #${ideaId}`, 'success');
      await refreshSummary();
    } else {
      setActionState(actionKey, 'error');
      setBanner({ tone: 'error', title: 'อัปเดตไอเดียไม่สำเร็จ', detail: result.error || `ไอเดีย #${ideaId}` });
    }
  };

  const openSettings = () => {
    setTempApiKey(apiKey);
    setTempApiUrl(apiUrl);
    setShowSettings(true);
  };

  const saveSettings = () => {
    setApiKey(tempApiKey);
    setApiUrl(tempApiUrl);
    setStoredSetting('admin_api_key', tempApiKey);
    setStoredSetting('admin_api_url', tempApiUrl);
    setShowSettings(false);
    setBanner({ tone: 'success', title: 'บันทึกการตั้งค่าแล้ว', detail: 'คำสั่งถัดไปจะใช้ API URL และ ADMIN_API_KEY ล่าสุด' });
    addActivity('บันทึกการตั้งค่าแล้ว', 'Dashboard จะใช้คีย์ล่าสุดกับคำสั่งถัดไป', 'success');
  };

  const sourceIssues = useMemo(
    () => summary.sources.items.filter((source) => source.health_status === 'empty' || source.health_status === 'stale'),
    [summary.sources.items],
  );

  const monitoringTiles = [
    { label: 'งานล่าสุด', value: statusLabel(summary.latest_job.status), meta: summary.latest_job.started_at || 'ยังไม่เคยรัน' },
    {
      label: 'แหล่งข้อมูล',
      value: `${summary.sources.ok}/${summary.sources.total} ปกติ`,
      meta: `${summary.sources.empty} ไม่มีข้อมูล, ${summary.sources.stale} ข้อมูลเก่า`,
    },
    { label: 'รายงาน', value: statusLabel(summary.report.status), meta: summary.report.report_date || 'ยังไม่มีรายงาน' },
    { label: 'Telegram', value: statusLabel(summary.telegram.status), meta: summary.telegram.sent_at || 'ยังไม่ส่ง' },
  ];

  const running = Boolean(activeAction);

  return (
    <div className="operator-shell">
      <aside className="operator-panel control-panel">
        <div className="brand-block">
          <div>
            <p className="eyebrow">เรดาร์คอนเทนต์ Advice</p>
            <h1>แดชบอร์ดผู้ดูแล</h1>
          </div>
          <button className="icon-button" onClick={openSettings} title="ตั้งค่า">ตั้งค่า</button>
        </div>

        <section className={`status-banner ${banner.tone}`} aria-live="polite">
          <div className="status-orb" />
          <div>
            <strong>{banner.title}</strong>
            <span>{banner.detail}</span>
          </div>
        </section>

        <section className="control-card">
          <div className="section-title">คำสั่งหลัก</div>
          <div className="action-stack">
            {PRIMARY_ACTIONS.map((action) => (
              <ActionButton
                action={action}
                key={action.key}
                state={actionStates[action.key] || 'idle'}
                disabled={running || (action.key === 'refresh' && isLoading)}
                onClick={() => void runAction(action)}
              />
            ))}
          </div>
          <button className="secondary-action compact-toggle" onClick={() => setShowMore((value) => !value)}>
            {showMore ? 'ซ่อนคำสั่งย่อย' : 'แสดงคำสั่งย่อย'}
          </button>
          {showMore && (
            <div className="more-actions">
              {MORE_ACTIONS.map((action) => (
                <ActionButton
                  action={action}
                  key={action.key}
                  state={actionStates[action.key] || 'idle'}
                  disabled={running}
                  onClick={() => void runAction(action)}
                  compact
                />
              ))}
            </div>
          )}
        </section>

        <section className="control-card activity-card">
          <div className="section-title">Activity Log</div>
          <div className="activity-list">
            {activityLog.map((entry) => (
              <div className={`activity-row ${entry.tone}`} key={entry.id}>
                <time>{entry.time}</time>
                <div>
                  <strong>{entry.title}</strong>
                  <span>{entry.detail}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="control-card">
          <div className="section-title">เช็กลิสต์ก่อนใช้งานจริง</div>
          {summary.production.checks.map((check) => (
            <div className="compact-row" key={check.key}>
              <span>{productionLabel(check.label)}</span>
              <span className={`pill ${check.configured ? 'ok' : 'warning'}`}>{check.configured ? 'พร้อม' : 'ยังไม่ได้ตั้งค่า'}</span>
            </div>
          ))}
        </section>
      </aside>

      <main className="operator-main">
        <section className={`office-stage ${running ? 'is-running' : ''}`}>
          {isAssetsLoaded && officeState ? (
            <OfficeCanvas
              officeState={officeState}
              onClick={(id) => {
                if (id !== null && id >= 0) {
                  setSelectedAgentId(id);
                }
              }}
              isEditMode={false}
              editorState={mockEditorState}
              onEditorTileAction={() => {}}
              onEditorEraseAction={() => {}}
              onEditorSelectionChange={() => {}}
              onDeleteSelected={() => {}}
              onRotateSelected={() => {}}
              onDragMove={() => {}}
              editorTick={editorTick}
              panRef={panRef}
              fitMode="width"
              zoomMultiplier={0.9671232}
              minZoom={0.85}
              panRatioY={-0.28}
            />
          ) : (
            <div className="loading-state">กำลังโหลดออฟฟิศ...</div>
          )}
          <div className={`workflow-line ${running || summary.latest_job.status === 'running' ? 'active' : ''}`} />
          <div className="stage-hud">
            <span>สถานะงาน</span>
            <strong>{activeAction?.phase || statusLabel(summary.latest_job.status)}</strong>
          </div>
          <div className="agent-bubbles">
            {AGENTS.map((agent) => (
              <div className={`agent-bubble agent-${agent.id} ${running ? 'working' : ''}`} key={agent.key}>
                <strong>{agent.name}</strong>
                <span>{agentStatus(agent.id, summary, activeAction)}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="monitoring-strip">
          {monitoringTiles.map((tile) => (
            <div className="monitor-tile" key={tile.label}>
              <span>{tile.label}</span>
              <strong>{tile.value}</strong>
              <small>{tile.meta}</small>
            </div>
          ))}
        </section>
      </main>

      <aside className="operator-panel detail-panel">
        <DetailCard title="ข้อมูลพนักงานออฟฟิศจำลอง" footer={selectedAgentId !== null ? "คลิกตัวอื่นเพื่อเปลี่ยนพนักงาน" : "คลิกที่ตัวพนักงานในออฟฟิศจำลองเพื่อดูข้อมูล"}>
          {selectedAgentId === null ? (
            <div className="empty-text" style={{ padding: '10px 0', textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🕵️‍♂️</div>
              คลิกเลือกพนักงานในออฟฟิศจำลอง<br />เพื่อดูรายละเอียดหน้าที่การทำงาน
            </div>
          ) : (() => {
            const meta = AGENTS_METADATA[selectedAgentId];
            if (!meta) return <p className="empty-text">ไม่พบข้อมูล</p>;
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', borderBottom: '1px solid var(--border-color, #444)', paddingBottom: '8px' }}>
                  <span style={{ fontSize: '2.5rem' }}>{meta.avatar}</span>
                  <div>
                    <strong style={{ display: 'block', fontSize: '1.1rem' }}>{meta.title}</strong>
                    <span style={{ fontSize: '0.85rem', color: '#888' }}>{meta.role}</span>
                  </div>
                </div>
                <div className="compact-row" style={{ marginTop: '4px' }}>
                  <span>สถานะปัจจุบัน:</span>
                  <span className={`pill ${activeAction ? 'running' : 'ok'}`} style={{ fontWeight: 'bold' }}>
                    {agentStatus(selectedAgentId, summary, activeAction)}
                  </span>
                </div>
                <p style={{ fontSize: '0.88rem', margin: '4px 0', lineHeight: '1.4', color: '#ccc' }}>
                  {meta.desc}
                </p>
                <div style={{ marginTop: '4px' }}>
                  <strong style={{ fontSize: '0.88rem', display: 'block', marginBottom: '4px' }}>หน้าที่หลัก:</strong>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.85rem', color: '#aaa', lineHeight: '1.4' }}>
                    {meta.bullets.map((b, idx) => (
                      <li key={idx} style={{ marginBottom: '2px' }}>{b}</li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })()}
        </DetailCard>

        <DetailCard title="สุขภาพแหล่งข้อมูล" footer="ดูแหล่งข้อมูลทั้งหมด">
          {summary.sources.items.slice(0, 6).map((source) => (
            <div className="compact-row" key={source.source_id}>
              <span title={source.reason}>{source.name}</span>
              <span className={`pill ${source.health_status}`}>{statusLabel(source.health_status)}</span>
              {(source.health_status === 'empty' || source.health_status === 'stale') && source.active && (
                <button className="inline-action" disabled={running} onClick={() => void disableSource(source)}>
                  {actionStates[`source-${source.source_id}`] === 'running' ? 'กำลังปิด...' : 'ปิดใช้'}
                </button>
              )}
            </div>
          ))}
          {sourceIssues.length === 0 && <p className="empty-text">แหล่งข้อมูลพร้อมใช้งาน</p>}
        </DetailCard>

        <DetailCard title="สรุปรายงานล่าสุด" footer="ดูรายงาน">
          <div className="compact-row"><span>สถานะ</span><span className={`pill ${summary.report.status}`}>{statusLabel(summary.report.status)}</span></div>
          <div className="compact-row"><span>วันที่</span><span>{summary.report.report_date || '-'}</span></div>
          <div className="compact-row"><span>โพสต์เด่น</span><span>{summary.report.top_posts_count}</span></div>
          <div className="compact-row"><span>ความยาวบรีฟ</span><span>{summary.report.message_length}</span></div>
        </DetailCard>

        <DetailCard title="ไอเดียที่บันทึกไว้" footer={`${summary.saved_ideas.saved} บันทึกแล้ว / ${summary.saved_ideas.used} ใช้แล้ว`}>
          {summary.saved_ideas.items.length === 0 ? (
            <p className="empty-text">ยังไม่มีไอเดียที่บันทึกไว้</p>
          ) : (
            summary.saved_ideas.items.map((idea) => (
              <div className="idea-row" key={idea.id}>
                <div>
                  <strong>{idea.title || `ไอเดีย #${idea.idea_number || idea.id}`}</strong>
                  <span>{statusLabel(idea.status)}</span>
                </div>
                {idea.status !== 'used' && (
                  <button className="inline-action" disabled={running} onClick={() => void markIdeaUsed(idea.id)}>
                    {actionStates[`idea-${idea.id}`] === 'running' ? 'กำลังบันทึก...' : 'ใช้แล้ว'}
                  </button>
                )}
              </div>
            ))
          )}
        </DetailCard>
      </aside>

      {showSettings && (
        <div className="settings-backdrop">
          <div className="settings-modal">
            <h2>ตั้งค่า API</h2>
            <label>
              URL ฐานของ API
              <input value={tempApiUrl} onChange={(event) => setTempApiUrl(event.target.value)} />
            </label>
            <div className="modal-actions">
              <button className="secondary-action" onClick={() => setShowSettings(false)}>ยกเลิก</button>
              <button className="primary-action" onClick={saveSettings}>บันทึก</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ActionButton({
  action,
  state,
  disabled,
  onClick,
  compact = false,
}: {
  action: ActionConfig;
  state: ActionState;
  disabled: boolean;
  onClick: () => void;
  compact?: boolean;
}) {
  const isRunning = state === 'running';
  return (
    <button
      className={`action-button ${action.primary ? 'primary' : 'secondary'} ${compact ? 'compact' : ''} ${state}`}
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      <span className="action-state-dot" />
      <span>
        <strong>{isRunning ? action.phase : action.label}</strong>
        {!compact && <small>{action.description}</small>}
      </span>
    </button>
  );
}

function DetailCard({ title, footer, children }: { title: string; footer: string; children: ReactNode }) {
  return (
    <section className="detail-card">
      <header>
        <h2>{title}</h2>
      </header>
      <div className="detail-card-body">{children}</div>
      <footer>{footer}</footer>
    </section>
  );
}

function getStoredSetting(key: string, fallback: string): string {
  try {
    return window.localStorage?.getItem(key) || fallback;
  } catch {
    return fallback;
  }
}

function setStoredSetting(key: string, value: string): void {
  try {
    window.localStorage?.setItem(key, value);
  } catch {
    // บาง browser context ปิด localStorage ได้ แต่ state ในหน้ายังใช้ต่อได้
  }
}

function summarizeActionOutcome(action: ActionConfig, data: Record<string, unknown> | OpsSummary): ActionOutcome {
  const payload = data as Record<string, unknown>;
  if ('skipped' in payload && payload.skipped) {
    return {
      state: 'error',
      tone: 'warning',
      title: `${action.label} ยังไม่เริ่ม`,
      detail: String(payload.skipped),
    };
  }

  if (action.key === 'refresh') {
    return {
      state: 'success',
      tone: 'success',
      title: `${action.label} สำเร็จ`,
      detail: action.description,
    };
  }

  if (action.key === 'send-telegram') {
    const sent = payload.sent === true;
    return {
      state: sent ? 'success' : 'error',
      tone: sent ? 'success' : 'error',
      title: sent ? 'ส่ง Telegram สำเร็จ' : 'ส่ง Telegram ไม่สำเร็จ',
      detail: sent ? 'รายงานล่าสุดถูกส่งเข้า Telegram แล้ว' : 'Telegram API ตอบกลับว่าไม่สามารถส่งรายงานได้',
    };
  }

  if (action.key === 'full-daily-run') {
    const collected = numberValue(payload.collected);
    const scored = numberValue(payload.scored);
    const analyzed = numberValue(payload.analyzed);
    const reportId = numberValue(payload.report_id);
    const telegramSent = payload.telegram_sent;
    const parts = [
      `ดึงโพสต์ใหม่ ${collected} รายการ`,
      `คำนวณคะแนน ${scored} รายการ`,
      `วิเคราะห์ ${analyzed} รายการ`,
      reportId > 0 ? `สร้างรายงาน #${reportId}` : 'ยังไม่พบรหัสรายงาน',
    ];

    if (telegramSent === true) parts.push('ส่ง Telegram แล้ว');
    if (telegramSent === false) parts.push('ส่ง Telegram ไม่สำเร็จ');

    return {
      state: telegramSent === false ? 'error' : 'success',
      tone: telegramSent === false ? 'warning' : 'success',
      title: telegramSent === false ? 'รันระบบครบ แต่ส่ง Telegram ไม่สำเร็จ' : 'รันระบบเต็มรูปแบบสำเร็จ',
      detail: parts.join(' / '),
    };
  }

  const detailParts = [
    payload.collected !== undefined ? `ดึงโพสต์ใหม่ ${numberValue(payload.collected)} รายการ` : null,
    payload.scored !== undefined ? `คำนวณคะแนน ${numberValue(payload.scored)} รายการ` : null,
    payload.analyzed !== undefined ? `วิเคราะห์ ${numberValue(payload.analyzed)} รายการ` : null,
    payload.report_id !== undefined ? `สร้างรายงาน #${numberValue(payload.report_id)}` : null,
  ].filter(Boolean);

  return {
    state: 'success',
    tone: 'success',
    title: `${action.label} สำเร็จ`,
    detail: detailParts.length > 0 ? detailParts.join(' / ') : action.description,
  };
}

function numberValue(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

function moveAgentsForAction(officeState: OfficeState, actionKey: string | null): void {
  const activeAgentIds = new Set(actionKey ? ACTION_AGENT_IDS[actionKey] || [] : []);
  for (const agent of AGENTS) {
    const isActive = activeAgentIds.has(agent.id);
    officeState.setAgentActive(agent.id, isActive);
    if (isActive) {
      officeState.sendToSeat(agent.id);
    } else {
      moveAgentToStandby(officeState, agent.id);
    }
  }
}

function moveAgentToStandby(officeState: OfficeState, agentId: number): void {
  const preferredTile = STANDBY_TILES[agentId] || STANDBY_TILES[0];
  if (officeState.walkToTile(agentId, preferredTile.col, preferredTile.row)) return;

  const fallbackTile = officeState.walkableTiles[(agentId * 7) % Math.max(officeState.walkableTiles.length, 1)];
  if (fallbackTile) officeState.walkToTile(agentId, fallbackTile.col, fallbackTile.row);
}

function apiErrorMessage(status: number): string {
  if (status === 401) return 'คีย์ผู้ดูแลระบบไม่ถูกต้องหรือยังไม่ได้ใส่ กรุณากดตั้งค่าแล้วใส่ ADMIN_API_KEY';
  if (status === 403) return 'ไม่มีสิทธิ์เรียกคำสั่งนี้ กรุณาตรวจสอบ ADMIN_API_KEY';
  return `เรียก API ไม่สำเร็จ (HTTP ${status})`;
}

function agentStatus(agentId: number, summary: OpsSummary, action: ActionConfig | null): string {
  if (action) {
    if (agentId === 1 && action.key === 'collect') return 'กำลังดึงข้อมูล';
    if (agentId === 2 && action.key === 'score') return 'กำลังคำนวณ';
    if (agentId === 3 && action.key === 'analyze') return 'กำลังวิเคราะห์';
    if (agentId === 4 && action.key === 'generate-report') return 'กำลังทำรายงาน';
    if (agentId === 5 && action.key === 'send-telegram') return 'กำลังส่ง';
    return 'กำลังทำงาน';
  }
  if (summary.latest_job.status === 'running') return 'กำลังทำงาน';
  if (agentId === 1 && summary.sources.empty > 0) return 'แหล่งข้อมูลว่าง';
  if (agentId === 1 && summary.sources.stale > 0) return 'ข้อมูลเก่า';
  if (agentId === 3 && summary.saved_ideas.saved > 0) return `${summary.saved_ideas.saved} ไอเดีย`;
  if (agentId === 4) return statusLabel(summary.report.status);
  if (agentId === 5) return statusLabel(summary.telegram.status);
  return agentId === 0 ? statusLabel(summary.latest_job.status) : 'ปกติ';
}

function statusLabel(status: string): string {
  return STATUS_LABELS[status] || status;
}

function productionLabel(label: string): string {
  return PRODUCTION_LABELS[label] || label;
}

function issueTitle(title: string): string {
  return productionLabel(title);
}

function formatTime(): string {
  return new Date().toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' });
}

export default App;
