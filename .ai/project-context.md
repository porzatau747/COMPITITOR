# Advice Content Radar Project Context

Advice Content Radar is an AI-powered automation system (MVP) custom-built for **Advice Sam Roi Yod** (ร้าน Advice สามร้อยยอด), a local IT store franchise branch in Prachuap Khiri Khan, Thailand. 

Its primary objective is to scrape public IT trend/competitor pages, compute metrics for virality and business relevance, generate localized daily content briefs (captions, carousel ideas, video scripts) that align with Advice Sam Roi Yod's services, and deliver them directly to store operators via a Telegram Bot every morning.

---

## Business Domain & Context

Advice Sam Roi Yod sells computers, notebooks, printers, network gear, CCTV, components (RAM, SSD, etc.), and offers diagnostic and repair services (e.g., PC upgrades, fixing slow systems). 

Traditional marketing requires manually searching local competitors or popular IT forums to find out what content gets engagement, which is time-consuming and prone to missing key localized angles. Advice Content Radar automates this process by:
1. **Aggregating signals** from selected sources.
2. **Filtering out noise** (e.g., general memes, mobile device drama, or news that cannot drive sales/repair visits to a local IT storefront).
3. **Translating hot topics** into ready-to-use marketing concepts optimized for the local Sam Roi Yod shop (e.g., highlighting pick-up & delivery, on-site diagnostics, or component upgrades over buying expensive new gear).

---

## Goals & Functional Scope

1. **Intelligent Curation**: Automate daily data collection from various competitor/industry platforms.
2. **Relevance-Driven Scoring**: Use a custom scoring engine to rate posts based on raw virality, local IT alignment, content freshness, and novelty relative to recently generated briefs.
3. **Localized AI Synthesis**: Generate actionable content ideas (specifically single-image captions, carousel layout ideas, and Reels/TikTok video drafts) written in Thai, incorporating local store calls to action (CTAs).
4. **Daily Morning briefings**: Send a formatted brief to the store owners on Telegram at 06:00 AM local time daily.
5. **Operational Health Monitoring**: Provide CLI/API dashboards to monitor whether external sources are successfully providing updates or going stale.

---

## Technical Stack

* **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
* **Database & ORM**: SQLite (for local MVP) and PostgreSQL support (with SQLAlchemy 2.0 ORM, migrations, and transfer helper scripts)
* **Pydantic**: Pydantic v2 Settings for configuration and schemas.
* **Scraping Frameworks**:
  * [CloakBrowser](https://github.com/colbymchenry/cloakbrowser) (primary Playwright browser automation with full stealth/bypass and humanize support for public pages)
  * [Scrapling](https://github.com/scrapling/scrapling) (fallback lightweight HTML scraper)
  * Meta Graph API (optional for authorized Facebook Pages)
* **AI Providers**: OpenAI SDK (compatible with generic APIs and direct Gemini content generation endpoint)
* **Task Scheduling**: APScheduler (BackgroundScheduler) with daily cron triggers, paired with local OS-level task triggers (e.g., Hermes crontab).
* **Communication Channel**: Telegram Bot API webhook and send-message services.
