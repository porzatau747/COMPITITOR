# Agent Bootstrap

Before performing ANY task:

## 1. Read Project Context

Read the following files in order:

1. .ai/project-context.md
2. .ai/architecture.md
3. .ai/project-map.md
4. .ai/coding-rules.md
5. .ai/karpathy-skills.md

Do not start implementation until all files are read.

---

## 2. Build Working Context

Summarize:

* project purpose
* architecture overview
* relevant services
* affected modules
* dependencies
* possible side effects

Identify what parts of the system may be impacted.

---

## 3. Follow Project Rules

Follow ALL rules defined in:

* coding-rules.md
* karpathy-skills.md

If instructions conflict:

1. coding-rules.md
2. architecture.md
3. karpathy-skills.md

in that priority order.

---

## 4. Perform Impact Analysis

Before modifying code:

### For business logic changes

Run:

* CodeGraph Context
* CodeGraph Callers
* CodeGraph Callees
* CodeGraph Impact Analysis

### For API changes

Identify:

* callers
* consumers
* request/response contracts

### For database changes

Identify:

* migrations
* repositories
* services
* API impact

### For shared utilities

Identify all dependent modules.

Do not edit code until impact analysis is complete.

---

## 5. Create Implementation Plan

Explain:

* what will be changed
* why it is needed
* affected files
* risks
* migration requirements

Wait for confirmation if the change is large or risky.

---

## 6. Create Safety Checkpoint

Before major modifications:

```bash
git status
git add -A
git commit -m "checkpoint: before <task>"
```

or create an equivalent checkpoint.

---

## 7. Implement Incrementally

Prefer:

* small commits
* minimal diffs
* reversible changes

Avoid large-scale rewrites unless explicitly requested.

---

## 8. Verify Changes

After implementation:

* run tests
* run lint
* verify build
* verify impacted workflows

Report:

* files changed
* impact summary
* verification results

---

## 9. Never Assume

If required information is missing:

* inspect the codebase
* inspect architecture
* inspect callers

Do not invent behavior.
Do not guess APIs.
Do not guess data structures.
