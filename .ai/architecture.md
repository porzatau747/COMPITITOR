# Advice Content Radar Architecture

This document describes the software architecture, data pipelines, scoring formulas, and security systems of the Advice Content Radar application.

---

## 1. Architectural Style & Core Modules

The application is structured as a modular, service-based Python project, built on **FastAPI** and **SQLAlchemy**. It follows a clear separation of concerns:

```
                  ┌────────────────────────┐
                  │      FastAPI App       │
                  │     (app/main.py)      │
                  └───────────┬────────────┘
                              │ Uses
                              ▼
        ┌──────────────────────────────────────────┐
        │                 Routers                  │
        │          (app/routers/*.py)              │
        └─────────────────────┬────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │             Services              │
            │        (app/services/*.py)        │
            └───────┬─────────────────────┬─────┘
                    │                     │
                    ▼                     ▼
        ┌───────────────────────┐ ┌──────────────┐
        │      Collectors       │ │  Database    │
        │ (app/collectors/*.py) │ │  & Models    │
        └───────────────────────┘ └──────────────┘
```

1. **API Layer (`app/routers/` & `app/main.py`)**: Defines FastAPI paths, tags, request validations, and authorization dependency gates.
2. **Business Logic Layer (`app/services/`)**: Implements functions for viral scoring, report generation, local adaptation, Telegram communications, memory retrieval, and operator dashboard summaries.
3. **Data Collection Layer (`app/collectors/`)**: Defines modules for fetching external posts using APIs, manual CSV uploads, or HTML scrapers.
4. **Data access Layer (`app/models/`, `app/schemas/`, `app/database.py`)**: Maps Python objects to SQL databases, sets unique constraints, and formats incoming/outgoing JSON schemas using Pydantic.
5. **Background Jobs (`app/jobs/`)**: Integrates APScheduler to schedule daily routines and encapsulates the orchestrator logic of the workflow.

---

## 2. The Data Pipeline

The core function of the application is a 5-step data workflow (`daily_workflow.py`):

```
┌──────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Collection  │ ──> │    Scoring    │ ──> │  AI Analysis  │ ──> │    Report     │ ──> │   Delivery    │
│   (Fetch)    │     │   (Ranking)   │     │  & Adaptation │     │  Generation   │     │  (Telegram)   │
└──────────────┘     └───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
```

### 1. Collection Phase
External content is collected from active sources. If `MOCK_MODE=true` is enabled, the pipeline generates dummy items using `MockCollector`. Otherwise, it triggers:
* **`WebAgentCollector`**: Queries public websites. It runs a `robots.txt` check via `RobotsCache`, discovers candidate article links matching `IT_KEYWORDS`, and fetches pages.
* **`FacebookGraphCollector`**: Queries the official Meta Graph API `/posts` endpoint for authorized pages using `FACEBOOK_PAGE_ACCESS_TOKEN`.
* **`FacebookCloakCollector`**: Scrapes public Facebook pages using Playwright (via `cloakbrowser`) using stealth, geolocation, and session cookies (`c_user` and `xs`).
* **`ManualImportCollector`**: Processes manual CSV or JSON uploads (used to ingest public competitor data without violating Terms of Service).

### 2. Scoring Phase
Every post in the database is evaluated and ranked by `score_post`. The score relies on:
* **Raw viral score**: Weighs engagement values (likes * 1 + comments * 3 + shares * 5 + views * 0.1).
* **Normalized score**: Divides raw score by the average raw score of all posts in the database.
* **Local relevance score**: Evaluates content focus. Posts matching high-priority IT keywords (e.g. Notebook, PC, Printer, SSD, Repair) gain scores, while generic, irrelevant keywords (e.g. mobile, drama, meme, smartphone) trigger a 35-point penalty.
* **Freshness score**: Decays the rating by 3 points per hour since the creation date.
* **Novelty score**: Computes Jaccard word similarity between the post and recently saved ideas (past 14 days) to prevent generating repetitive briefings.
* **Final score**: Combines metrics using a weighted average: `Engagement (Capped 0-100) * 0.4 + Local Relevance * 0.4 + Freshness * 0.1 + Novelty * 0.1`.

### 3. AI Analysis & Local Adaptation
The pipeline selects the top 5 highest-ranked posts. If they do not have an existing analysis:
1. It calls OpenAI or Gemini (direct API endpoint) to extract the post's structure: core hook, hook type, content type, pain point, and why it worked, as well as risks.
2. If the AI model fails, it falls back to a template-based `mock_analyze_post` response and appends a warning to the `risk` list.
3. It passes the analysis to `adapt_for_advice`, which structures a custom angle for **Advice Sam Roi Yod** (e.g., adding local calls to action: free pick-up/delivery, hardware upgrades).
4. The local draft is added to `ContentMemory` to influence the next run's novelty score.

### 4. Report Generation
The `DailyReport` compiles:
* Summary of the day's primary market signals (categories).
* Metadata of top 5 posts, why they succeeded, risks, and local adaptations.
* Standardized actions for the day (Sales, Knowledge, Reels/TikTok ideas).
* High-performing marketing hooks.
* A formatted string brief tailored for Telegram rendering.

### 5. Delivery Phase
The generated morning brief is sent to Telegram using `send_report`.
* Because Telegram imposes a strict limit of 4096 characters per message, the application runs a custom `split_telegram_message` function, splitting long briefs by newlines (`\n`) and space characters without truncating words.
* It retries delivery up to 3 times on failures.
* Upon successful delivery, it updates `telegram_sent_at` in the database.

---

## 3. Security Hardening

The application incorporates multi-layer security protections for deployment readiness:

### API Access Security
1. **Admin Header Guard**: If `ADMIN_API_KEY` is configured in `.env`, FastAPI dependencies block all non-health and non-webhook endpoints unless requests contain a matching `X-Admin-API-Key` header.
2. **Telegram Webhook Secret Validation**: Webhook updates from Telegram are validated by verifying the `X-Telegram-Bot-Api-Secret-Token` header matches `TELEGRAM_WEBHOOK_SECRET`.
3. **Chat ID Allowlist**: If `ALLOWED_TELEGRAM_CHAT_IDS` is defined, the webhook rejects command updates originating from unauthorized chat accounts, returning an HTTP 403 Forbidden.

### SSRF Protection in Web Scraper
The `WebAgentCollector` includes a strict IP verification mechanism (`_is_safe_public_url`) before executing any GET requests:
* It checks the hostname and resolves its DNS records.
* If a resolved IP points to private, loopback, link-local, multicast, or reserved ranges (e.g., `127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`), it flags the URL as unsafe and skips it. This prevents Server-Side Request Forgery (SSRF) attacks targeting local services.

### Scraping Compliance
The scraper reads external `robots.txt` rules using `RobotsCache` and respects crawl restrictions. It runs under a dedicated User-Agent (`AdviceContentRadarBot`) and adds delays between page requests (`delay_seconds`) to avoid rate-limiting or overloading public sites.
