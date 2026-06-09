---
name: reviewing-pr-code
description: Use when requested to review a Pull Request, audit code changes, or perform a codebase review before deployment
---

# Reviewing PR Code

## Overview

A systematic approach to reviewing Pull Requests or codebase changes that ensures high quality, security, and maintainability. The goal is to provide constructive, actionable feedback while clearly distinguishing between critical blockers and minor suggestions.

## When to Use

- When the user asks you to "review this PR" or "review this code"
- When auditing a codebase for vulnerabilities, performance issues, or bugs
- When providing feedback on a teammate's or sub-agent's code changes before merging

## Core Focus Areas (What to check)

1. **Logic & Bugs:** Verify the code meets business requirements. Look for edge cases, unhandled exceptions, and silent failures.
2. **Security:** Check for basic vulnerabilities (SQL Injection, XSS) and leaked secrets (API Keys, passwords in plain text). Ensure credentials are not committed.
3. **Code Style:** Ensure consistent naming conventions, project structure, and strict type safety (e.g., avoiding explicit `any` in TypeScript).
4. **Test & Performance:** Verify unit test coverage. Identify performance bottlenecks (e.g., heavy sorting in renders, nested loops, missing memoization).

## Quick Reference: Output Format

When delivering the review, strictly categorize your feedback using visual tags:

- **[🚨 ต้องแก้ (Blocker)]**: Critical issues that will break the build, cause security breaches, or fail business requirements.
- **[💡 เสนอแนะ (Suggestion/Nitpick)]**: Code style improvements, performance optimizations, or nice-to-have features.

**For every piece of feedback, always provide:**
1. **The Problem:** What is wrong or could be improved.
2. **The Reason:** Why it matters (e.g., "If we change X to Y, it will help prevent Z").
3. **The Solution:** How to fix it, or testing steps to verify.

## Common Mistakes

| Mistake | Correction |
|---------|------------|
| Saying "this is bad code" | Be constructive: "If we use a Union Type here, it will prevent runtime errors." |
| Mixing nitpicks with blockers | Clearly label `[Blocker]` so the developer knows what is mandatory to fix before merging. |
| Reviewing without checking tests | Always verify if the PR includes corresponding tests for the new logic, or remind the author to add them. |
| Making assumptions about intent | Ask clarifying questions if the business logic of a change is unclear before demanding a rewrite. |
