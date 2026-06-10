# Coding Rules

## Required Reading

Before starting any task, always read:

* .ai/project-context.md
* .ai/architecture.md
* .ai/project-map.md
* .ai/coding-rules.md

---

## CodeGraph Requirements

For changes involving:

* business logic
* agents
* services
* APIs
* database
* shared utilities

Required steps:

1. Run CodeGraph query on the target symbol.
2. Run CodeGraph callers.
3. Run CodeGraph impact.
4. Summarize:

   * files involved
   * dependencies
   * impact radius
   * risks

If impact affects more than 5 files:

* stop
* explain why
* ask for confirmation

For simple UI, styling, copywriting, and visual changes:

* skip CodeGraph analysis

---

## Safety Rules

Never:

* modify environment secrets
* modify production databases directly
* delete large groups of files
* change package manager configuration without approval

---

## Development Workflow

Before major changes:

1. Create git checkpoint

Before editing:

1. Explain implementation plan

After editing:

1. Run build
2. Run lint
3. Run tests (if available)

Provide:

* summary of changes
* files modified
* risks introduced

---

## Documentation Rules

When creating new modules:

* update project-map.md
* update architecture.md if architecture changes

Do not leave documentation outdated.

## Required Thinking Style

Always follow:
- .ai/karpathy-skills.md


---

## Mandatory Analysis Rule

Before modifying any code:

1. Read the current implementation.
2. Understand the existing behavior.
3. Identify callers and dependencies.
4. Identify downstream impact.
5. Verify assumptions using code, not guesses.
6. Explain findings before editing.

Never modify code based solely on assumptions.

CodeGraph analysis does not replace source code inspection.

---

## Refactoring Rule

Prefer extending existing code over creating new systems.

Before creating:

* new service
* new utility
* new abstraction
* new framework layer

check whether an existing solution already exists.

Avoid:

* duplicate logic
* parallel implementations
* unnecessary abstractions
* code duplication

Reuse existing patterns whenever possible.

---

## Architecture Preservation Rule

Respect the existing architecture.

Do not:

* bypass service layers
* introduce architectural shortcuts
* couple unrelated modules
* violate dependency boundaries

If a change requires architectural deviation:

1. Explain why.
2. Describe the tradeoffs.
3. Request approval before implementation.

---

## Change Scope Rule

Prefer the smallest safe change that solves the problem.

Avoid:

* unnecessary rewrites
* large-scale refactors unrelated to the task
* touching unrelated files

Keep diffs focused and easy to review.

---

## Debugging Rule

When fixing bugs:

1. Identify the root cause.
2. Explain the root cause.
3. Verify the fix addresses the cause.
4. Verify no regressions are introduced.

Do not apply speculative fixes.

---

## Code Quality Rule

Prioritize:

* readability
* maintainability
* simplicity
* consistency with the existing codebase

Avoid clever solutions when a simpler solution is sufficient.

---

## Agent Behavior Rule

When requirements are unclear:

1. Inspect the codebase.
2. Inspect related modules.
3. Gather evidence.
4. Present findings.

Do not invent APIs.
Do not invent business logic.
Do not invent data structures.
Do not assume behavior without verification.
