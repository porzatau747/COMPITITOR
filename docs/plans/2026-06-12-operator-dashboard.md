# Operator Dashboard Implementation Plan

> **For Codex:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Build an operator-first dashboard with pixel-office status visualization, operational health summaries, source issue handling, report/Telegram visibility, and a small saved-ideas workflow.

**Architecture:** Add a small backend ops summary layer that aggregates existing jobs, reports, sources, config, and saved ideas into one dashboard-friendly contract. Keep existing routers/services intact where possible, and update the React/Vite dashboard to consume the summary and existing action endpoints incrementally.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic-style dictionaries currently used by routers, SQLite/PostgreSQL-compatible ORM models, React 19, TypeScript, Vite, existing pixel office canvas/assets.

---

## Preconditions

- Do not implement the scraping-risk recommendation.
- Do not edit `.env` secrets.
- Do not mutate production databases directly.
- Existing frontend lint changes are currently unstaged; do not revert or overwrite them.
- Before implementation, decide whether to continue in the current dirty worktree or create an isolated worktree.

## Task 1: Add Ops Summary Service Tests

**Files:**
- Create: `tests/test_ops_summary.py`
- Create or modify after RED: `app/services/ops_summary_service.py`

**Step 1: Write failing tests**

Create tests for these behaviors:

```python
def test_ops_summary_marks_stale_running_job(db_session):
    # Create JobRun(status="running", started_at older than stale threshold)
    # Summary should expose latest_job.status == "stale"
    # Summary should include top issue "Daily workflow stuck"
```

```python
def test_ops_summary_marks_report_outdated_and_telegram_not_sent(db_session):
    # Create DailyReport(report_date yesterday, telegram_sent_at None)
    # Summary should include report.status == "outdated"
    # Summary should include telegram.status == "not_sent"
```

```python
def test_ops_summary_counts_source_health(db_session):
    # Create active source with no posts, active source with recent post, inactive source
    # Summary should include source counts for ok, empty, inactive
```

**Step 2: Run RED**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_ops_summary.py -q
```

Expected: fail because `app.services.ops_summary_service` does not exist.

**Step 3: Implement minimal service**

Create `app/services/ops_summary_service.py` with:

- `build_ops_summary(db: Session) -> dict`
- helper functions kept private
- no new database tables
- no direct secret value exposure

The returned shape should be stable enough for the frontend:

```python
{
    "latest_job": {"status": "...", "name": "...", "started_at": "...", "finished_at": "...", "error": "..."},
    "sources": {"total": 0, "ok": 0, "empty": 0, "stale": 0, "inactive": 0, "items": [...]},
    "report": {"status": "...", "report_date": "...", "message_length": 0, "top_posts_count": 0},
    "telegram": {"status": "...", "sent_at": "..."},
    "saved_ideas": {"total": 0, "saved": 0, "used": 0, "items": [...]},
    "production": {"checks": [...]},
    "top_issues": [...]
}
```

**Step 4: Run GREEN**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_ops_summary.py -q
```

Expected: pass.

## Task 2: Expose Ops Summary API

**Files:**
- Create: `app/routers/ops.py`
- Modify: `app/main.py`
- Test: `tests/test_ops_summary.py`

**Step 1: Add failing API test**

Add a FastAPI test that requests:

```text
GET /ops/summary
```

Expected response contains keys:

- latest_job
- sources
- report
- telegram
- saved_ideas
- production
- top_issues

**Step 2: Run RED**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_ops_summary.py -q
```

Expected: route returns 404.

**Step 3: Implement route**

Create `app/routers/ops.py`:

- protect with existing admin dependency pattern
- call `build_ops_summary(db)`
- return dict directly

Register router in `app/main.py`.

**Step 4: Run GREEN**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_ops_summary.py -q
```

Expected: pass.

## Task 3: Source Disable Action

**Files:**
- Inspect: `app/routers/sources.py`
- Modify only if needed: `app/routers/sources.py`, `app/schemas/source_schema.py`
- Test: existing source tests or `tests/test_ops_summary.py`

**Step 1: Verify existing update route**

Confirm whether `PUT /sources/{source_id}` can set `active=false` without requiring unrelated fields.

**Step 2: If existing route is sufficient**

Do not add backend code. Use it from frontend.

**Step 3: If existing route is not sufficient, write failing test**

Test that a partial update can disable a source:

```python
response = client.put(f"/sources/{source.id}", json={"active": False})
assert response.status_code == 200
assert response.json()["active"] is False
```

Then implement the smallest backend change.

## Task 4: Frontend Data Contract

**Files:**
- Modify: `frontend/src/App.tsx`
- Create if useful: `frontend/src/types/ops.ts`

**Step 1: Add TypeScript types**

Create types matching `/ops/summary`:

- `OpsSummary`
- `OpsIssue`
- `SourceHealthItem`
- `SavedIdeaSummaryItem`
- status string unions where useful

**Step 2: Replace scattered derived dashboard data**

Fetch `/ops/summary` on refresh and after actions.

Keep existing fetches only where still needed for detailed lists.

**Step 3: Verify TypeScript**

Run:

```powershell
npm.cmd run build
```

Expected: TypeScript compiles.

## Task 5: Operator Dashboard Layout

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.css`

**Step 1: Implement layout shell**

Build:

- left control panel
- central pixel office area at about 60%
- bottom monitoring strip
- right detail panel

Keep panel text short and avoid nested card-heavy layout.

**Step 2: Add controls**

Left panel primary controls:

- Run Daily
- Send Telegram
- Refresh
- More

`More` reveals:

- Collect
- Score
- Analyze
- Generate Report
- Send Telegram

**Step 3: Add monitoring strip**

Tiles:

- Latest Job
- Sources
- Report
- Telegram

**Step 4: Add right detail cards**

Cards:

- Top Issues
- Sources Health
- Latest Report Summary

Use the user-provided card style direction: icon + title, compact rows, status pills, footer link/action.

**Step 5: Verify**

Run:

```powershell
npm.cmd run lint
npm.cmd run build
```

Expected: both pass.

## Task 6: Pixel Office Status Map

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.css`
- Possibly inspect: `frontend/src/office/**`

**Step 1: Map ops statuses to agents**

Map:

- Pop: overall command state
- Mina: source health / collection
- Leo: scoring / post counts
- Sam: AI analysis / saved ideas
- Ava: report status
- Uploader: Telegram status

**Step 2: Add bubbles**

Use short bubbles:

- running
- OK
- source empty
- report stale
- not sent
- sent

**Step 3: Add lightweight animation classes**

Use CSS animations for workflow path and activity hints. Do not refactor the canvas engine unless required.

**Step 4: Verify**

Run:

```powershell
npm.cmd run lint
npm.cmd run build
```

Expected: both pass.

## Task 7: Saved Ideas Mini Panel

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.css`

**Step 1: Show saved idea summary**

Use `/ops/summary` saved idea counts and recent items.

**Step 2: Add Mark Used action**

Call existing:

```text
POST /ideas/{idea_id}/used
```

After success, refresh `/ops/summary`.

**Step 3: Empty state**

Show:

```text
No saved ideas yet
```

**Step 4: Verify**

Run:

```powershell
npm.cmd run lint
npm.cmd run build
```

Expected: both pass.

## Task 8: Production Checklist

**Files:**
- Modify: `app/services/ops_summary_service.py`
- Test: `tests/test_ops_summary.py`
- Modify: `frontend/src/App.tsx`

**Step 1: Add tests**

Test that production checks expose only boolean/masked status and never secret values.

**Step 2: Implement service checks**

Check configuration presence only.

**Step 3: Surface warnings**

Add missing production checklist items to `top_issues` or right panel card.

**Step 4: Verify**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_ops_summary.py -q
npm.cmd run lint
npm.cmd run build
```

Expected: all pass.

## Task 9: End-To-End Verification

**Files:**
- No code change unless verification exposes a bug.

**Step 1: Backend tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests -q
```

Expected: all pass. Existing `.pytest_cache` permission warning may remain.

**Step 2: Frontend verification**

Run:

```powershell
npm.cmd run lint
npm.cmd run build
```

Expected: both pass.

**Step 3: Manual API check**

Run local server if needed and inspect:

```text
GET /ops/summary
```

Expected: returns dashboard contract without secret values.

**Step 4: Final report**

Report:

- changed files
- statuses implemented
- tests/build/lint results
- remaining limitations

