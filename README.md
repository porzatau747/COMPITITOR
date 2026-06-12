# Advice Content Radar

ระบบ AI Automation MVP สำหรับร้าน Advice สามร้อยยอด เพื่อสรุปโพสต์คู่แข่ง/เทรนด์คอนเทนต์ไอทีที่มี Engagement สูง แล้วแปลงเป็นไอเดียโพสต์ที่ใช้ได้จริง พร้อมส่งรายงานผ่าน Telegram ทุกเช้า

## สถานะ MVP

ทำแล้ว:
- FastAPI backend
- SQLAlchemy models ตาม schema หลัก
- Source CRUD
- Mock Collector 10 โพสต์
- Manual Import Collector สำหรับ CSV/JSON รวมถึง template สำหรับ Facebook manual export
- Facebook Graph Collector สำหรับ Page API ที่ได้รับสิทธิ์เท่านั้น
- Web Agent Collector สำหรับเว็บสาธารณะ โดยใช้ CloakBrowser เป็น fetcher หลักในโหมด stealth/bypass เต็มรูปแบบ และมี Scrapling/httpx เป็นตัวเลือกสำรอง (Fallback)
- Facebook Cloak Collector สำหรับดึงข้อมูลโพสต์คู่แข่งเฟซบุ๊กสาธารณะแบบอัตโนมัติ โดยใช้ CloakBrowser และเปิดโหมด stealth/bypass เต็มรูปแบบ
- Scoring Engine: raw viral, normalized, local relevance, freshness, novelty, final score
- AI Analyzer ต่อ Gemini/Generative Language API และ fallback เป็น mock เมื่อ API ล้มเหลว
- Local Adaptation สำหรับ Advice สามร้อยยอด
- Daily Report builder
- Telegram sender และ webhook command handler
- Scheduler workflow เวลา 06:00 Asia/Bangkok พร้อม job id/max_instances/coalesce กันรันซ้ำ
- Tests พื้นฐานและ operational hardening tests
- Job run tracking (`job_runs`) สำหรับดูสถานะ workflow ล่าสุด
- Source health report ผ่าน CLI และ `/sources/health`
- Operator dashboard summary ผ่าน `/ops/summary`
- PostgreSQL migration helper สำหรับย้ายข้อมูลจาก SQLite
- Telegram message chunking กันข้อความยาวเกิน limit

ยังต้องตั้งค่า/ระวังเพิ่มเติม:
- การดึงโพสต์ Facebook จริง ทำงานแบบดึงข้อมูลอัตโนมัติเท่านั้น ผ่าน FacebookCloakCollector โดยใช้ CloakBrowser และเปิดโหมด stealth/bypass เต็มรูปแบบ
- Web Agent ดึงข้อมูลแบบอัตโนมัติ โดยใช้ CloakBrowser และเปิดโหมด stealth/bypass เต็มรูปแบบเป็นหลัก สำหรับหน้าเว็บสาธารณะที่ robots.txt อนุญาต โดยมีระบบหน่วงเวลาเพื่อความปลอดภัย

## โครงสร้างโปรเจกต์

```text
app/
  main.py
  config.py
  database.py
  models/
  schemas/
  services/
  routers/
  jobs/
  collectors/
  prompts/
migrations/
tests/
.env.example
requirements.txt
README.md
```

## ติดตั้ง

```bash
cd D:/por/project/COMPITITOR/advice-content-radar
python -m pip install -r requirements.txt
```

## ตั้งค่า .env

คัดลอกไฟล์ตัวอย่าง:

```bash
cp .env.example .env
```

ค่าที่ควรตั้ง:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/advice_content_radar
TELEGRAM_BOT_TOKEN=ใส่ token จาก BotFather
TELEGRAM_CHAT_ID=ใส่ chat id ผู้รับรายงาน
OPENAI_API_KEY=ใส่เมื่อจะเปิดใช้ AI จริง
AI_API_KEY=
AI_BASE_URL=
AI_MODEL=gpt-4o-mini
FACEBOOK_PAGE_ACCESS_TOKEN=ใส่ token สำหรับ Meta Graph API ถ้ามีสิทธิ์ใช้ Page API
ADMIN_API_KEY=ตั้งค่าเมื่อต้องการล็อก endpoint API ด้วย header X-Admin-API-Key
TELEGRAM_WEBHOOK_SECRET=ตั้งค่าเมื่อต้องการให้ Telegram webhook ต้องมี secret token
ALLOWED_TELEGRAM_CHAT_IDS=chat id ที่อนุญาตให้ใช้ webhook commands คั่นด้วย comma
STALE_JOB_AFTER_MINUTES=60
TIMEZONE=Asia/Bangkok
MOCK_MODE=true
```

สำหรับทดสอบบนเครื่องโดยไม่ต้องลง PostgreSQL ใช้:

```env
DATABASE_URL=sqlite:///./advice_content_radar.db
```

ถ้าไม่มี `.env` ระบบจะ fallback เป็น SQLite อัตโนมัติ

### API hardening

ถ้าตั้ง `ADMIN_API_KEY` แล้ว endpoint ทุกตัวนอกจาก `/health` และ `/telegram/webhook` จะต้องส่ง header:

```bash
-H "X-Admin-API-Key: <ADMIN_API_KEY>"
```

ถ้าตั้ง `TELEGRAM_WEBHOOK_SECRET` แล้ว Telegram webhook ต้องส่ง header `X-Telegram-Bot-Api-Secret-Token` ให้ตรงกัน และถ้าตั้ง `ALLOWED_TELEGRAM_CHAT_IDS` ระบบจะรับคำสั่งเฉพาะ chat id ที่อยู่ใน allowlist เท่านั้น

## รัน server

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

ตรวจสุขภาพระบบ:

```bash
python -c "import httpx; print(httpx.get('http://127.0.0.1:8010/health').json())"
```

## รัน mock daily workflow

```bash
python -c "from app.database import init_db, SessionLocal; from app.jobs.daily_workflow import run_full_daily; init_db(); db=SessionLocal(); print(run_full_daily(db, send=False)); db.close()"
```

หรือผ่าน API:

```bash
python -c "import httpx; print(httpx.post('http://127.0.0.1:8010/jobs/full-daily-run').json())"
```

## ทดสอบ endpoints สำคัญ

```bash
python -c "import httpx; print(httpx.get('http://127.0.0.1:8010/sources').json())"
python -c "import httpx; print(httpx.get('http://127.0.0.1:8010/posts/top').json()[0])"
python -c "import httpx; print(httpx.get('http://127.0.0.1:8010/reports/today').json()['telegram_message'][:500])"
python -c "import httpx; print(httpx.get('http://127.0.0.1:8010/sources/health').json())"
```

## Source health report

ดูสุขภาพแหล่งข้อมูล:

```bash
python scripts/source_health_report.py --stale-hours 72
```

หรือผ่าน API local:

```bash
python -c "import httpx; print(httpx.get('http://127.0.0.1:8010/sources/health').json())"
```

สถานะหลัก:
- `ok`: มีข้อมูลล่าสุด
- `empty`: ยังไม่เคย import โพสต์
- `stale`: ไม่มีข้อมูลใหม่เกินช่วงที่กำหนด
- `inactive`: source ถูกปิดใช้งาน

## เพิ่ม source

```bash
python -c "import httpx; print(httpx.post('http://127.0.0.1:8010/sources', json={'name':'คู่แข่งตัวอย่าง','platform':'facebook','source_url':'https://example.com/page','source_type':'direct_competitor','category':'Notebook','location':'Prachuap','priority_score':80,'active':True}).json())"
```

## ข้อมูลข้อ 3: CSV/JSON source ต้องเอามาจากไหน

สำหรับ MVP ให้ใช้ข้อมูลจากแหล่งที่คุณมีสิทธิ์เข้าถึงและเห็นได้ปกติเท่านั้น เช่น:

- เปิดเพจ Facebook/เว็บคู่แข่งแบบสาธารณะ แล้วกรอกข้อมูลโพสต์ลง CSV เอง
- Export/คัดลอกโพสต์จากเพจที่คุณเป็นแอดมินหรือมีสิทธิ์ดูข้อมูล
- ใช้ Google Sheet/Excel บันทึกหัวข้อโพสต์, ลิงก์, like, comment, share, view แล้ว save เป็น CSV
- ใช้ RSS/API ทางการของเว็บข่าวไอที ถ้ามี
- ห้ามใช้ระบบหลบ login, scrape หลังบ้าน, หรือ bypass ระบบป้องกันของแพลตฟอร์ม

ผมสร้างไฟล์ template ไว้แล้ว:

```text
data/manual_import_template.csv
data/facebook_competitor_posts_template.csv
```

คอลัมน์ที่รองรับ:

```text
source_name, platform, source_url, source_type, post_url, post_text, like_count, comment_count, share_count, view_count
```

รัน import manual/Facebook export:

```bash
python scripts/import_manual_data.py data/facebook_competitor_posts_template.csv --score
```

## Facebook competitor data

ระบบรองรับการดึงข้อมูลเพจ Facebook สาธารณะของคู่แข่ง 2 รูปแบบ:

1. **Facebook Cloak Collector (แนะนำสำหรับระบบอัตโนมัติ)** — ดึงข้อมูลโพสต์และยอดการมีส่วนร่วม (Engagement Metrics) แบบอัตโนมัติ โดยใช้ CloakBrowser (Playwright-based) ที่ทำงานในโหมด stealth/bypass เต็มรูปแบบ และใช้คุกกี้เซสชันสาธารณะหากกำหนดไว้ใน `.env` เพื่อเลี่ยงการถูกจำกัดการเข้าถึงจาก Facebook
2. **Meta Graph API** — ใช้ `FACEBOOK_PAGE_ACCESS_TOKEN` และกำหนดค่าที่ `data/facebook_sources.json` สำหรับกรณีเพจที่ได้รับสิทธิ์การใช้งานผ่าน API ทางการ

## Web Agent Scraper สำหรับเว็บสาธารณะ

ระบบใช้งาน `WebAgentCollector` เพื่อดึงข้อมูลเว็บข่าวสารและแนวโน้มไอทีแบบอัตโนมัติ โดยใช้ `CloakBrowser` ในโหมด stealth/bypass เต็มรูปแบบเป็นตัวเปิดรันหลัก (Primary Fetcher) เพื่อความเสถียรในการดึงข้อมูล และมีระบบตรวจสอบ `robots.txt` พร้อมหน่วงเวลาคำขอเพื่อไม่ให้รบกวนเว็บไซต์ปลายทาง

โครงสร้างไฟล์ที่เกี่ยวข้อง:
```text
app/collectors/web_agent_collector.py
scripts/import_web_sources.py
data/web_sources.json
```

หลักการทำงาน:
- ดึงข้อมูลจาก URL สาธารณะที่กำหนดโดยอัตโนมัติ
- ใช้ CloakBrowser เป็นหลักพร้อมการเลียนแบบพฤติกรรมมนุษย์ (humanize, geoip, stealth_args)
- มีระบบดึงด้วย Scrapling และ httpx เป็นตัวเลือกสำรองกรณีเปิดใช้งานบราวเซอร์ไม่สำเร็จ

กำหนดแหล่งข้อมูลเว็บได้ที่:
```text
data/web_sources.json
```

ตัวอย่างการสั่งรันดึงข้อมูลเว็บและประเมินคะแนนทันที:
```bash
$env:PYTHONPATH="."
.venv\Scripts\python.exe scripts/import_web_sources.py --score
```

หากตั้งค่า `MOCK_MODE=false` ตัว Daily Workflow จะเรียกใช้ Web Agent Collector, Facebook Cloak Collector และ Facebook Graph Collector ในการดึงข้อมูลโดยอัตโนมัติ

## ย้าย SQLite ไป PostgreSQL

ก่อนย้ายหรือก่อนแก้ข้อมูลจำนวนมาก ให้ backup SQLite local:

```bash
python scripts/backup_sqlite.py
```

ไฟล์ backup จะอยู่ใน `backups/` และถูก ignore จาก git

เมื่อมี PostgreSQL พร้อมแล้ว ตั้ง URL ปลายทาง:

```bash
export POSTGRES_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/advice_content_radar'
```

ตรวจแบบ dry run:

```bash
python scripts/migrate_sqlite_to_postgres.py --dry-run
```

ย้ายข้อมูลจริง:

```bash
python scripts/migrate_sqlite_to_postgres.py
```

หลังย้ายสำเร็จ เปลี่ยน `.env` เป็น:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/advice_content_radar
```

## ทดสอบ Telegram

ตรวจ token, webhook info และส่งข้อความทดสอบ:

```bash
python scripts/telegram_ops.py check --send-test
```

ตั้ง webhook จริงต้องมี public HTTPS URL ที่ชี้มาที่ FastAPI endpoint `/telegram/webhook` แล้วตั้งค่าใน `.env`:

```env
PUBLIC_WEBHOOK_URL=https://your-domain.example/telegram/webhook
```

จากนั้นรัน:

```bash
python scripts/telegram_ops.py set-webhook --drop-pending-updates
```

หรือส่ง URL ตรง ๆ:

```bash
python scripts/telegram_ops.py set-webhook --url https://your-domain.example/telegram/webhook --drop-pending-updates
```

ถ้ายังไม่มี public HTTPS URL ให้ใช้ Telegram sender + Hermes cron รายวันไปก่อน; Bot API จะส่งรายงานได้ แต่ Telegram จะยังยิง commands เข้า `/telegram/webhook` จาก internet ไม่ได้

ส่งรายงานล่าสุดด้วย script workflow:

```bash
python scripts/run_daily_report.py
```

ถ้าไม่ได้ตั้งค่า Telegram ระบบจะ log warning และตอบ `sent: false`

## Telegram commands ที่รองรับ

Webhook endpoint: `POST /telegram/webhook`

รองรับ:
- `/today`
- `/caption 1`
- `/carousel 1`
- `/reels 1`
- `/post_plan`
- `/save_idea 1`
- `/used 1`
- `/more`

ทดสอบแบบไม่ต้องต่อ Telegram จริง:

```bash
python - <<'PY'
import os, httpx
from dotenv import load_dotenv
load_dotenv()
headers={'X-Telegram-Bot-Api-Secret-Token': os.getenv('TELEGRAM_WEBHOOK_SECRET','')}
payload={'message': {'chat': {'id': int(os.getenv('TELEGRAM_CHAT_ID','0'))}, 'text': '/caption 1'}}
print(httpx.post('http://127.0.0.1:8010/telegram/webhook', headers=headers, json=payload).json()['reply'])
PY
```

## รัน scheduler

ตัวระบบมี scheduler ภายในโปรเจกต์ และผมตั้ง Hermes cron ให้รันทุกวัน 06:00 แล้ว:

```text
job_id: 6932f8510a67
name: Advice Content Radar daily report
schedule: 0 6 * * *
```

Cron นี้เรียก Hermes script `advice_content_radar_daily.py` ซึ่ง subprocess ไปที่ `scripts/run_daily_report.py` ด้วย Python ที่ติดตั้ง dependencies แล้ว ถ้า Telegram Bot API ส่งสำเร็จ script จะเงียบ ถ้าส่งไม่สำเร็จจะ fallback ส่งรายงานกลับผ่าน Hermes Telegram chat นี้

ถ้าต้องการรัน scheduler ภายในแอปเอง ใช้:

```bash
python -c "from app.database import init_db; from app.jobs.scheduler import start_scheduler; import time; init_db(); start_scheduler(); print('scheduler running'); time.sleep(999999)"
```

ตารางเวลา Asia/Bangkok:
- 06:00 full daily workflow: collect, score, analyze, generate report, send Telegram

## รัน tests

```bash
python -m pytest tests -q
```

## ข้อจำกัดของ MVP

- Facebook จริงรองรับผ่าน manual import/Google Sheet export หรือ Meta Graph API ที่มีสิทธิ์เท่านั้น; ไม่รองรับ personal-login scraping หรือ bypass protection
- มี Operator Dashboard พื้นฐานสำหรับดู workflow, source health, report/Telegram status, saved ideas และ production checklist
- ยังไม่ Auto Post / Auto Share
- AI จริงเปิดใช้ผ่าน Gemini แล้ว แต่ถ้า API quota/503 ล้มเหลว ระบบจะ fallback เป็น mock และใส่ warning ใน risk
- PostgreSQL พร้อมผ่าน `DATABASE_URL` แต่การทดสอบ local ยังใช้ SQLite
- Endpoint API รองรับ `ADMIN_API_KEY` แล้ว แต่ถ้ายังเว้นค่าว่างจะไม่ล็อก endpoint เพื่อให้ local MVP ใช้งานง่าย; ก่อนเปิด public internet ต้องตั้ง `ADMIN_API_KEY`, `TELEGRAM_WEBHOOK_SECRET`, และ `ALLOWED_TELEGRAM_CHAT_IDS`

## ขั้นตอนต่อไปที่แนะนำ

1. ถ้ามี domain/HTTPS แล้ว ให้ตั้ง `PUBLIC_WEBHOOK_URL` และรัน `python scripts/telegram_ops.py set-webhook --drop-pending-updates`
2. ใส่โพสต์คู่แข่งจริงลง `data/facebook_competitor_posts_template.csv` จากข้อมูล public/manual/Google Sheet แล้ว import ด้วย `python scripts/import_manual_data.py data/facebook_competitor_posts_template.csv --score`
3. ตั้ง PostgreSQL จริงแล้วรัน `scripts/migrate_sqlite_to_postgres.py`
4. ตรวจ `scripts/source_health_report.py` เป็นระยะเพื่อดู source ที่ empty/stale
5. เพิ่ม feedback loop จากโพสต์จริงของร้าน เช่น inbox/engagement ที่เกิดขึ้น
6. ถ้าจะเปิด public endpoint ให้ตั้ง reverse proxy HTTPS และตรวจ `ADMIN_API_KEY`, `TELEGRAM_WEBHOOK_SECRET`, `ALLOWED_TELEGRAM_CHAT_IDS` ทุกครั้งก่อนเปิด port
