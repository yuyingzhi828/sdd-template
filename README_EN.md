# SDD Template — Spec-Driven Development Starter Kit

> **In the age of AI-generated code, natural language is the new programming language.**  
> A design document is no longer just for humans — it's a **System Prompt for your AI**.  
> 99% of AI-generated garbage code comes from unclear context and missing constraints.  
> This template locks AI inside well-defined boundaries so it can build fast without breaking things.

**Spec-Driven Development (SDD)** starter kit — built for the AI-assisted development era.  
Turn "what to build, how to verify it, and who can change what" into trackable, machine-checkable files.  
Eliminate AI hallucinations. Prevent scope creep. Protect working code.

---

## Why This Exists

| Pain Point | Solution |
|------------|----------|
| AI modifies files it shouldn't | `LOCK.md` + `lock-check.py` blocks commits at the gate |
| Requirements live in chat history | `RFC.md` is the single source of truth, with REQ-NNN IDs |
| Change scope keeps expanding | `propose.py` forces every change to start with a written proposal |
| Can't tell what module affects what | `impact.py` auto-scans dependencies and reports risk level |
| Architecture constraints live only in someone's head | `CONSTITUTION.md` + `arch-check.py` enforces rules on every commit |
| AI ignores your rules | `.cursorrules` makes Cursor/Copilot/Claude Code read the constraints automatically |

---

## Directory Structure

```
sdd-template/
├── .cursorrules                 # AI assistant constraints (auto-read by Cursor/Copilot)
├── .github/workflows/
│   └── sdd-check.yml            # CI: arch-check + lock-check on every push/PR
├── README.md                    # Chinese README
├── README_EN.md                 # This file
├── CONSTITUTION.md              # Project constitution: tech stack, architecture rules, anti-patterns
├── LICENSE                      # MIT
├── specs/
│   └── project-000-template/   # One directory per project or subsystem
│       ├── RFC.md               # Requirements spec — single source of truth, REQ-NNN numbered
│       ├── PLAN.md              # Implementation plan: Sprint list, milestones
│       ├── LOCK.md              # Lock registry: which files are frozen + unlock requests
│       ├── RFC_CHANGELOG.md     # Requirement change history, appended on every archive
│       ├── changes/
│       │   ├── active/          # In-flight change proposals (CH-NNN/)
│       │   └── archive/         # Completed and archived change proposals
│       └── sprints/
│           └── sprint-001-template/
│               ├── TASKS.md     # Sprint task list + done criteria
│               ├── REVIEWS.md   # Sprint retrospective
│               └── tasks/
│                   └── TK-001-template.md   # Single task card
├── governance/
│   ├── propose.py               # Generate change proposals (CH-NNN)
│   ├── impact.py                # Assess change impact, check LOCK conflicts
│   ├── apply-and-archive.py     # Advance change state: draft → in-progress → archived
│   ├── arch-check.py            # Architecture layer compliance check
│   ├── lock-check.py            # Locked file protection check
│   └── pre-commit.sh            # Git pre-commit hook — chains all checks
├── example/
│   └── project-url-shortener/  # Full example: URL shortener with one archived change (CH-001)
└── tests/
```

---

## Quickstart

### Step 1 — Copy the template

```bash
cp -r sdd-template/ my-new-project/
cd my-new-project/
git init
```

### Step 2 — Fill in CONSTITUTION.md

Edit `CONSTITUTION.md`:
- One-line project description
- Actual tech stack with versions
- Architecture hard rules
- AI usage constraints

### Step 3 — Rename the spec directory

```bash
mv specs/project-000-template specs/project-001-your-project-name
```

Update project ID references inside RFC.md, PLAN.md, LOCK.md.

### Step 4 — Write your first RFC

Edit `specs/project-001-xxx/RFC.md`.  
Divide into functional domains (F1, F2, ...) and write `REQ-001`, `REQ-002`... entries.

### Step 5 — Install the pre-commit hook

```bash
cp governance/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Step 6 — Drop .cursorrules in your project root

If you use Cursor, GitHub Copilot, or Claude Code, the `.cursorrules` file will be auto-read.  
Your AI assistant will follow all constraints without you having to repeat them every session.

---

## The Change Lifecycle

```
Requirement change needed
         │
         ▼
① Propose  →  python3 governance/propose.py project-001 "Add CSV export" --description "..."
              Generates: changes/active/CH-NNN/proposal.md + delta.md
         │
         ▼
② Fill delta.md  →  Specify exact RFC additions / modifications / deletions (REQ-NNN level)
         │
         ▼
③ Assess impact  →  python3 governance/impact.py project-001 CH-001
                     Generates: impact.md — locked file conflicts + dependency risk level
         │
         ▼
④ Apply  →  python3 governance/apply-and-archive.py project-001 CH-001 apply
            Interactive confirm → status: draft → in-progress
         │
         ▼
⑤ Implement  →  Follow TK task cards. git commit triggers arch-check + lock-check via CI.
         │
         ▼
⑥ Archive  →  python3 governance/apply-and-archive.py project-001 CH-001 archive
              Moves to archive/, appends RFC_CHANGELOG.md
              Reminder: merge delta.md back into RFC.md manually
```

---

## Script Reference

| Script | Example | Description |
|--------|---------|-------------|
| `propose.py` | `python3 governance/propose.py project-001 "Add export" --description "CSV format"` | Generate change proposal, auto-assign CH-NNN |
| `impact.py` | `python3 governance/impact.py project-001 CH-001` | Scan change impact, check lock conflicts |
| `apply-and-archive.py` | `python3 governance/apply-and-archive.py project-001 CH-001 apply` | Confirm implementation, draft → in-progress |
| `arch-check.py` | `python3 governance/arch-check.py` | Verify architecture layer compliance |
| `lock-check.py` | `git diff --cached --name-only \| python3 governance/lock-check.py` | Block commits that touch locked files |

---

## The Mental Model

```
Humans write the Constitution (CONSTITUTION.md) and the Goals (RFC.md)
AI does the work (Tasks / Code)
Scripts act as the police (Governance / Hooks / CI)
```

This is **human-AI collaborative development with guardrails** — not vibe coding.

---

## Real-World Example

See [`example/project-url-shortener/`](./example/) for a complete walkthrough:
- Full RFC with Mermaid ER diagram + architecture diagram
- 3-sprint plan with all tasks completed
- LOCK.md with one unlock request (approved)
- Archived change `CH-001: add custom alias` — proposal → delta → tasks, all filled out

---

## AI Tooling Integration

**Cursor / GitHub Copilot / Claude Code**  
Copy `.cursorrules` to your project root. The AI assistant reads it automatically and follows all constraints without manual prompting.

**GitHub Actions**  
`.github/workflows/sdd-check.yml` runs `arch-check` and `lock-check` on every push and PR.  
Even if a developer bypasses the local pre-commit hook with `--no-verify`, the cloud check still catches violations.

---

## Contributing

Issues and PRs welcome. This template is intentionally minimal and language-agnostic.  
The governance scripts use Python standard library only — no dependencies to install.

---

## License

MIT — free to use in commercial projects.
