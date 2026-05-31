# Wanman

A multi-agent platform for autonomous repository takeover and maintenance.

Wanman orchestrates a team of specialized AI agents that collaborate to maintain, improve, and advance a codebase — from triaging issues to shipping code — with minimal human intervention.

## Architecture

### Agent Roles

| Agent | Responsibility |
|-------|---------------|
| **CEO** | Initiative management, task decomposition, progress monitoring |
| **CTO** | Technical review, PR approval (≥95% coverage gate), architecture decisions |
| **Dev** | Code implementation, testing, branch management |
| **Feedback** | Quality analysis, metric tracking, improvement suggestions |
| **Marketing** | Documentation, changelogs, external communication |

### Core Concepts

- **Initiative** — A high-level goal that groups related work (e.g. "Improve test coverage").
- **Task** — A scoped unit of work within an initiative, tied to specific files or directories.
- **Capsule** — A change container that bounds a task's code modifications before they expand into a branch/PR.

```
Initiative
 └── Task
      └── Capsule (file-scoped changes → branch → PR)
```

### Workflow

1. CEO creates initiatives and decomposes them into tasks.
2. Dev agents claim tasks, create capsules, and implement changes on feature branches.
3. CTO reviews PRs against the coverage gate and merges approved work.
4. Feedback agent monitors quality metrics and surfaces improvement opportunities.
5. Agents continuously mine the codebase, docs, and TODOs for the next batch of high-value work.

## Quick Start

### Prerequisites

- Git and [GitHub CLI](https://cli.github.com/) (`gh`) authenticated
- Access to the wanman platform

### Bootstrapping

```bash
# Clone the repository
git clone <repo-url>
cd <repo>

# Initialize wanman
wanman init

# View active initiatives
wanman initiative list

# View tasks
wanman task list

# Assign a task to yourself
wanman task assign <task-id>
```

### Creating Work

```bash
# Create an initiative
wanman initiative create --title "Improve error handling"

# Create a scoped task
wanman task create --initiative <id> --title "Add retry logic to API client" --path src/api/

# Create a capsule to bound the changes
wanman capsule create --task <id> --initiative <id> --paths src/api/client.ts src/api/client.test.ts
```

### Branch & PR

```bash
git checkout -b wanman/<task-slug>
# ... implement changes ...
git push -u origin wanman/<task-slug>
gh pr create --title "feat: add retry logic to API client"
```

## Documentation

- [Architecture Overview](docs/architecture.md) — detailed system design and agent interactions
- [Contributing Guide](CONTRIBUTING.md) — how to contribute to this project

## License

See [LICENSE](LICENSE) for details.
