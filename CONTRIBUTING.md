# Contributing to Wanman

Thank you for your interest in contributing to Wanman! This guide covers everything you need to know to get your changes merged.

## Getting Started

### Prerequisites

- Git and [GitHub CLI](https://cli.github.com/) (`gh`) authenticated
- Access to the wanman platform
- Familiarity with the [Architecture Overview](docs/architecture.md)

### Fork and Clone

1. Fork the repository on GitHub.
2. Clone your fork locally:

   ```bash
   git clone https://github.com/<your-username>/wanman.git
   cd wanman
   ```

3. Add the upstream remote:

   ```bash
   git remote add upstream https://github.com/wanman/wanman.git
   ```

4. Keep your fork up to date before starting work:

   ```bash
   git fetch upstream
   git checkout master
   git merge upstream/master
   ```

## Branch Naming

All branches **must** follow the convention:

```
wanman/<task-slug>
```

- `wanman/` — required prefix for all contribution branches.
- `<task-slug>` — a short, lowercase, hyphenated description of the work.

Examples:

| Task | Branch Name |
|------|-------------|
| Add retry logic to API client | `wanman/add-retry-logic` |
| Fix null pointer in task parser | `wanman/fix-null-task-parser` |
| Expand README with setup instructions | `wanman/expand-readme-setup` |

Create your branch from `master`:

```bash
git checkout -b wanman/<task-slug> master
```

## Making Changes

1. **Claim or create a task** (if using wanman tooling):

   ```bash
   wanman task assign <task-id>
   wanman capsule create --task <id> --initiative <id> --paths <files>
   ```

2. **Implement your changes** on the feature branch. Keep changes scoped to the task.

3. **Write or update tests** for every change (see [Test Coverage Gate](#test-coverage-gate) below).

4. **Run the full test suite with coverage** before pushing:

   ```bash
   # Adjust to your project's test runner
   npm test -- --coverage    # or: pytest --cov, go test -cover, cargo tarpaulin
   ```

5. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/):

   ```
   <type>: <description>

   <optional body>
   ```

   Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

   Examples:

   ```
   feat: add retry logic to API client
   fix: handle null task ID in parser
   docs: expand README with setup instructions
   ```

## Pull Request Process

### Opening a PR

Push your branch and open a pull request:

```bash
git push -u origin wanman/<task-slug>
gh pr create --title "<type>: <description>"
```

### PR Checklist

Every PR must satisfy **all** of the following before it will be reviewed:

- [ ] Branch follows the `wanman/<task-slug>` naming convention.
- [ ] Commits follow Conventional Commits format.
- [ ] All tests pass locally.
- [ ] Test coverage meets the [95% gate](#test-coverage-gate).
- [ ] Changes are scoped to a single task or initiative.
- [ ] New or changed functionality includes corresponding tests.
- [ ] Documentation is updated if behavior or public APIs changed.

### PR Description

Include in your PR description:

1. **What** — a summary of the change.
2. **Why** — the motivation or linked initiative/task ID.
3. **How** — a brief implementation note if the change is non-trivial.
4. **Test plan** — how reviewers can verify the change.

## Test Coverage Gate

**All pull requests must maintain at least 95% test coverage.**

The CTO agent (or a human reviewer) enforces this gate during code review. PRs below the threshold will be **rejected** until coverage is brought up.

```bash
# Check coverage before pushing
npm test -- --coverage
# or
pytest --cov --cov-report=term-missing
# or
go test -coverprofile=coverage.out ./... && go tool cover -func=coverage.out
```

If your change touches untestable code (e.g. platform-specific I/O), document the exception in the PR and the reviewer may grant a waiver.

## Code Review Expectations

### For Authors

- Keep PRs small and focused — one task per PR.
- Respond to review feedback promptly.
- Mark conversations as resolved when addressed.
- Do not merge your own PRs.

### For Reviewers

- Review within **2 business days** of PR submission.
- Evaluate against the following criteria:

  | Priority | Criteria |
  |----------|----------|
  | **Critical** | Correctness, security vulnerabilities, data loss risk |
  | **High** | Test coverage ≥ 95%, edge case handling, error paths |
  | **Medium** | Code clarity, naming, adherence to project patterns |
  | **Low** | Style nits, minor refactors |

- Use the `Request changes` status for Critical and High issues.
- Use comment threads for Medium and Low suggestions.
- Approve only when all Critical and High items are resolved.

### Review Flow

```
Dev opens PR
  → CTO reviews (coverage gate + code quality)
    → Approved → merge
    → Changes requested → Dev addresses feedback → re-review
```

## Agent-Specific Guidelines

If you are contributing via the wanman agent platform:

| Agent | Responsibility |
|-------|---------------|
| **CEO** | Creates initiatives and tasks; does **not** merge PRs |
| **CTO** | Reviews PRs against the coverage gate; approves or requests changes |
| **Dev** | Implements changes, writes tests, opens PRs |
| **Feedback** | Monitors quality metrics; surfaces improvement opportunities |
| **Marketing** | Maintains docs, changelogs, and external communication |

## Questions?

Open an issue or reach out to the maintainers. We are happy to help you get started.
