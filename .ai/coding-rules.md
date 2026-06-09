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
