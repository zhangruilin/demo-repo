# Architecture Overview

This document describes how the Wanman platform is structured, how its agents collaborate, and how work flows from idea to merged code.

## Agent Roles

Wanman coordinates five specialized agents. Each owns a distinct responsibility and communicates through structured artifacts (initiatives, tasks, capsules, PRs).

| Agent | Role | Key Actions |
|-------|------|-------------|
| **CEO** | Strategic leadership | Creates initiatives, decomposes them into tasks, monitors progress, refreshes backlog |
| **CTO** | Technical authority | Reviews PRs, enforces the >=95% test-coverage gate, makes architecture decisions |
| **Dev** | Implementation | Claims tasks, creates capsules, writes code and tests on feature branches, opens PRs |
| **Feedback** | Quality analysis | Tracks metrics, surfaces improvement opportunities, identifies regressions |
| **Marketing** | Communication | Maintains documentation, changelogs, and external-facing content |

### Interaction Model

```
         ┌──────────┐
         │   CEO    │  owns initiatives & tasks
         └────┬─────┘
              │ assigns tasks
              ▼
         ┌──────────┐     opens PR     ┌──────────┐
         │   Dev    │ ──────────────── ▶│   CTO    │
         └──────────┘                   └────┬─────┘
              ▲                              │ approves / requests changes
              │                              ▼
         ┌──────────┐                   ┌──────────┐
         │Feedback  │  quality signals  │Marketing │
         └──────────┘                   └──────────┘
```

## Initiative / Task Hierarchy

Work is organized in a strict hierarchy that ensures traceability from high-level goals down to individual file changes.

### Initiative

An **initiative** is a high-level goal that groups related work (e.g. "Improve test coverage", "Add API documentation"). Initiatives are created and owned by the CEO.

### Task

A **task** is a scoped unit of work within an initiative. Each task is tied to specific files or directories using `--path` or `--pattern`. Tasks can be reassigned freely between agents.

### Capsule

A **capsule** is a change container that bounds a task's code modifications before they expand into a branch and PR. Every PR-sized code change must be represented as a capsule before branch work begins. Code changes must not leave the capsule boundary — if out-of-scope work is discovered, a follow-up task and capsule should be created.

```
Initiative ("Improve error handling")
 ├── Task: "Add retry logic to API client"        [path: src/api/]
 │    └── Capsule: src/api/client.ts, src/api/client.test.ts
 ├── Task: "Add error boundaries to UI"            [path: src/ui/]
 │    └── Capsule: src/ui/error-boundary.tsx, src/ui/error-boundary.test.tsx
 └── Task: "Update error handling docs"            [path: docs/]
      └── Capsule: docs/error-handling.md
```

## Capsule Workflow

The capsule workflow ensures that every change is scoped, reviewed, and merged through a consistent pipeline.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. Create  │───▶│  2. Branch  │───▶│ 3. Implement│───▶│  4. PR      │───▶│  5. Merge   │
│  Capsule    │    │  Feature    │    │  Code+Tests │    │  Review     │    │  Deploy     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

1. **Create Capsule** — CEO or Dev creates a capsule scoped to the task's file paths.
2. **Branch** — Dev creates a feature branch (`wanman/<task-slug>`) from `master`.
3. **Implement** — Dev writes code and tests within the capsule boundary, runs tests with coverage.
4. **PR Review** — Dev opens a PR. CTO reviews against the coverage gate (>=95%) and code quality standards.
5. **Merge** — CTO approves and merges, or requests changes. Dev iterates until approved.

### Branch Naming

All feature branches follow the pattern: `wanman/<task-slug>`

### Coverage Gate

PRs must maintain >=95% test coverage to be eligible for merge. The CTO enforces this gate during review.

## Takeover Process

The takeover process is how Wanman continuously advances a repository with minimal human intervention.

### Bootstrapping

1. Initialize the platform on a target repository.
2. CEO analyzes the codebase structure, existing docs, TODOs, and build pipelines.
3. CEO reverse-engineers a roadmap from code gaps and documentation state.

### Continuous Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                        Takeover Loop                            │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Identify │──▶│ Plan     │──▶│ Execute  │──▶│ Review   │    │
│  │ Gaps     │   │ Work     │   │ Changes  │   │ & Merge  │    │
│  └──────────┘   └──────────┘   └──────────┘   └────┬─────┘    │
│       ▲                                             │          │
│       └─────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

1. **Identify Gaps** — Mine codebase, docs, TODOs, scripts, and build pipelines for high-value work.
2. **Plan Work** — Create or refresh initiatives and decompose into scoped tasks with capsules.
3. **Execute Changes** — Dev agents implement on feature branches within capsule boundaries.
4. **Review & Merge** — CTO reviews PRs; approved work merges to `master`.
5. **Repeat** — Return to gap identification. When a metric reaches a local optimum, move to the next high-value area.

### Operating Principles

- Keep 1-3 active initiatives on the mission board at all times.
- Every loop, verify that the current backlog advances real product goals, roadmap, release readiness, or user value.
- When all current tasks are complete, immediately refresh initiatives from roadmap, README/docs, code structure, TODOs, build pipelines, and release gaps.
- Tasks may be reassigned freely, but code changes must not leave capsule boundaries.
- All agents write analysis results to their own `output/` directory; actual code/doc changes happen at the repo root.
