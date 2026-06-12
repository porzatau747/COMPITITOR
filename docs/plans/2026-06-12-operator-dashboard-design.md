# Operator Dashboard Design

**Goal:** Build an operator-first dashboard for Advice Content Radar that makes the morning workflow status obvious, keeps the pixel office as the main visual surface, and exposes only the actions needed to recover common operational issues.

**Approved scope:**
- Use vertical slices in this order: operational health, report/Telegram consistency, source empty handling, dashboard layout, saved ideas mini panel, production checklist, and first feedback loop.
- Do not include the scraping-risk documentation/workflow item.
- Do not add per-source collect in the first phase.
- Do not add full approve/reject/note feedback in the first phase.
- Do not edit secrets or production databases directly.

## Layout

Use an Operator Dashboard layout based on mockup option 1.

- Center: pixel office, about 60% of the total screen.
- Left: compact Control Panel.
- Bottom: Monitoring Strip.
- Right: Detail Panel with compact cards.

The interface should feel playful and cute, but remain readable and calm enough for daily operator use.

## Pixel Office

Use six agents:

1. Pop Owner
2. Mina Scraper
3. Leo Scoring
4. Sam Creative AI
5. Ava Report
6. Uploader Telegram

Arrange them by workflow:

`Pop -> Mina -> Leo -> Sam -> Ava -> Uploader`

When a job is running, show both:

- workflow path animation between agents
- lightweight agent-specific activity animation

Example states:

- Pop: clipboard / command bubble
- Mina: typing / search bubble
- Leo: score meter / chart bubble
- Sam: lightbulb / idea sparkle
- Ava: checklist / report stack
- Uploader: paper plane / Telegram bubble

Warnings/errors should appear as short bubbles near the relevant agent.

## Left Control Panel

Show three primary actions:

- Run Daily
- Send Telegram
- Refresh

Add a `More` control that reveals detailed commands:

- Collect
- Score
- Analyze
- Generate Report
- Send Telegram

The first screen must not show all detailed commands at once.

## Bottom Monitoring Strip

Show four compact tiles:

- Latest Job
- Sources
- Report
- Telegram

Each tile should include a short status, timestamp/count where useful, and a status color.

## Right Detail Panel

Use three compact cards with a style similar to the user-provided reference image:

1. Top Issues
2. Sources Health
3. Latest Report Summary

Cards should use:

- icon + title headers
- compact rows
- status pills on the right
- pastel status colors
- footer link/action such as `View all sources`, `View report`, or `Resolve issues`

## Operational Health

The dashboard reads state from API endpoints, not SQLite directly.

It should surface:

- latest job status
- start/finish time
- stale job warning
- latest error
- recommended next action

A running job older than the configured stale threshold should be presented as an issue.

## Report And Telegram

Show:

- report date
- top post count
- Telegram brief length
- Telegram sent time
- status: OK, Not Sent, Outdated, or Too Long

If the latest report is not for today, show `Report outdated`.

If a report exists but is not sent, show `Telegram not sent`.

## Source Empty Handling

For empty sources such as `comcraft.ds`:

- show the source in Top Issues and Sources Health
- provide a `Disable` action
- require a short confirmation before disabling
- refresh dashboard state after disabling

Use the existing source update behavior if it is sufficient.

## Saved Ideas Mini Panel

Show saved ideas without making the dashboard crowded:

- count/status appears in monitoring/detail context
- mini panel lists recent saved ideas
- each saved idea can be marked used
- empty state: `No saved ideas yet`

Use existing `/ideas/saved` and `/ideas/{idea_id}/used` behavior where possible.

## Production Checklist

Show a masked operational checklist only. Do not expose secret values.

Possible checks:

- ADMIN_API_KEY configured
- TELEGRAM_WEBHOOK_SECRET configured
- ALLOWED_TELEGRAM_CHAT_IDS configured
- Telegram token/chat id configured
- database URL type

Missing values should become warnings, not blockers for local MVP.

## Feedback Loop

First phase feedback loop is based on `SavedIdea.used_at`.

Do not add a new engagement-feedback table yet. After real usage exists, a later phase can add notes and metrics such as reach, comments, and sales inquiries.

## Testing Strategy

- Backend tests for ops summary statuses and stale job handling.
- Backend tests for report/Telegram summary mapping.
- Backend tests for source disable behavior only if new backend behavior is needed.
- Frontend lint/build for UI changes.
- Existing backend test suite must continue passing.

