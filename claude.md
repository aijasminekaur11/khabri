# Claude Project Operating Rules

This document defines **non-negotiable structure, workflow, and governance rules** for this project. Once execution starts, these rules must be followed consistently throughout the lifecycle.

**This file is the SOURCE OF TRUTH. If any instruction conflicts with this file, claude.md wins.**

---

## 1. PURPOSE

* Enforce clean structure, disciplined testing, and traceable debugging
* Enable 4 independent CLIs to work in parallel without confusion
* Ensure deterministic execution with full traceability
* Maintain test-first discipline across all development

---

## 2. PROJECT WORKING DIRECTORY (MANDATORY)

**All work must be performed in:**

```
D:\Jasmine\00001_Content_app\News_Update
```

🚫 **Absolute Rules**:

* NO operations outside this directory
* ALL file paths must be relative to this root
* ALL folders and files created must be within this directory
* This is the **project-root** referenced throughout this document

---

## 3. DIRECTORY STRUCTURE (FINAL & PERMANENT)

```
/project-root
│
├── claude.md                    # This file (source of truth)
├── README.md                    # High-level project overview only
│
├── src/                         # Production-ready code only
│   ├── __init__.py
│   ├── config/                  # CLI 1: Config Manager
│   ├── processors/              # CLI 1: Processor Pipeline
│   ├── orchestrator/            # CLI 1: Main Orchestrator
│   ├── scrapers/                # CLI 2: All scrapers
│   │   ├── news_scraper.py
│   │   ├── rss_reader.py
│   │   ├── competitor_tracker.py
│   │   └── igrs_scraper.py
│   └── notifiers/               # CLI 3: All notifiers
│       ├── telegram_notifier.py
│       ├── email_notifier.py
│       └── keyword_engine.py
│
├── testing/                     # ALL testing & debugging
│   ├── test_plan.md             # Mandatory test plan
│   ├── test_cases/              # Individual test cases
│   ├── issues/                  # Auto-generated issue files
│   ├── debug_logs/              # Debug logs per issue
│   ├── fixtures/                # Mock data for tests
│   └── sandbox/                 # Experimental / throwaway tests
│
├── logs/                        # Phase & decision logs
│   ├── phase_01.log
│   ├── cli_1.log
│   ├── cli_2.log
│   ├── cli_3.log
│   ├── cli_4.log
│   └── debug_summary.log
│
├── docs/                        # Architecture, decisions, references
│   ├── BLUEPRINT.md             # Full technical documentation
│   ├── FEATURE_SUMMARY.md       # Feature list & workflow
│   ├── project_state.json       # CENTRAL STATE FILE
│   └── contracts/               # Interface contracts
│       ├── config_schema.md
│       ├── event_payloads.md
│       └── notifier_interface.md
│
└── scripts/                     # Utility / automation scripts only
```

🚫 **Rules**:

* NO experimental files in `src/`
* NO ad-hoc files in root
* NO skipping `testing/` for quick fixes
* NO unnecessary documentation files

---

## 4. CLI DEFINITIONS & RESPONSIBILITIES

### 4.1 CLI Overview

| CLI | Name | Responsibility | Status Check |
|-----|------|----------------|--------------|
| **CLI 1** | Core Builder | Main development | Read `project_state.json` |
| **CLI 2** | Scraper Builder | Data collection | Read `project_state.json` |
| **CLI 3** | Notifier Builder | Output & delivery | Read `project_state.json` |
| **CLI 4** | Test Runner | Testing & QA | Read `project_state.json` |

### 4.2 CLI 1 — Core Builder

**Responsibility**: Main development & core infrastructure

**Owned Modules**:
- `src/config/` — Config Manager
- `src/processors/` — Processor Pipeline
- `src/orchestrator/` — Main Orchestrator

**Authority**:
- Defines core contracts (other CLIs consume)
- Creates shared utilities
- Establishes project patterns

**Dependencies**: None (starts first)

**Definition of Done**:
- [ ] All owned modules implemented
- [ ] Unit tests written and passing
- [ ] Contracts published in `/docs/contracts/`
- [ ] Logs updated in `/logs/cli_1.log`
- [ ] State file updated
- [ ] No BLOCKED items

### 4.3 CLI 2 — Scraper Builder

**Responsibility**: Data collection from all sources

**Owned Modules**:
- `src/scrapers/news_scraper.py`
- `src/scrapers/rss_reader.py`
- `src/scrapers/competitor_tracker.py`
- `src/scrapers/igrs_scraper.py`

**Authority**:
- Implements all data fetching logic
- Defines scraper-specific error handling
- Manages rate limiting

**Dependencies**:
- **HARD**: CLI 1 must complete `config/` module first
- **SOFT**: Can stub processor interfaces

**Definition of Done**:
- [ ] All scrapers implemented
- [ ] Unit tests with mocked responses
- [ ] Integration tests with fixtures
- [ ] Logs updated in `/logs/cli_2.log`
- [ ] State file updated
- [ ] No BLOCKED items

### 4.4 CLI 3 — Notifier Builder

**Responsibility**: Output formatting & delivery

**Owned Modules**:
- `src/notifiers/telegram_notifier.py`
- `src/notifiers/email_notifier.py`
- `src/notifiers/keyword_engine.py`

**Authority**:
- Implements all notification logic
- Defines message templates
- Manages external API connections

**Dependencies**:
- **HARD**: CLI 1 must complete `config/` module first
- **SOFT**: Can stub processor outputs

**Definition of Done**:
- [ ] All notifiers implemented
- [ ] Unit tests with mocked APIs
- [ ] Template tests passing
- [ ] Logs updated in `/logs/cli_3.log`
- [ ] State file updated
- [ ] No BLOCKED items

### 4.5 CLI 4 — Test Runner

**Responsibility**: Testing, QA, and validation

**Authority**:
- **CAN BLOCK** any CLI from proceeding
- **CAN FAIL** builds and merges
- **CAN GENERATE** issue files for other CLIs
- Owns ALL test files in `/testing/`

**Special Powers**:
- May read ALL code from any CLI
- May run tests against any module
- May reject incomplete work
- May create issues in `/testing/issues/`

**Dependencies**: None (runs independently)

**Definition of Done**:
- [ ] All test suites passing
- [ ] Coverage reports generated
- [ ] No open HIGH priority issues
- [ ] Logs updated in `/logs/cli_4.log`
- [ ] State file updated

---

## 5. CENTRAL PROJECT STATE (MANDATORY)

### 5.1 State File Location

```
/docs/project_state.json
```

### 5.2 State File Rules

1. **ALL CLIs must read this file before starting work**
2. Each CLI may update **ONLY its own section**
3. State changes must be atomic (read → modify → write)
4. Waiting decisions must be based on this file
5. No CLI may proceed if its dependencies show `BLOCKED` or `TODO`

### 5.3 State Values

| Status | Meaning |
|--------|---------|
| `TODO` | Not started |
| `IN_PROGRESS` | Currently being worked on |
| `BLOCKED` | Waiting on dependency |
| `DONE` | Completed and validated |
| `FAILED` | Failed, needs intervention |

---

## 6. DEPENDENCY & WAITING PROTOCOL

### 6.1 Dependency Types

| Type | Behavior |
|------|----------|
| **HARD** | CLI must wait until dependency is `DONE` |
| **SOFT** | CLI may proceed with mocks/stubs |

### 6.2 Waiting Rules

1. If dependency not met → mark self as `BLOCKED` and **STOP**
2. No polling loops
3. No repeated execution attempts
4. No questions asked (unless explicitly permitted)
5. Log the block and wait for state change

### 6.3 Dependency Matrix

```
CLI 1 (Core)      → No dependencies (starts first)
CLI 2 (Scrapers)  → HARD depends on CLI 1 config/
CLI 3 (Notifiers) → HARD depends on CLI 1 config/
CLI 4 (Testing)   → No dependencies (runs anytime)
```

---

## 7. BLOCKED CLI BEHAVIOR (STAY ALIVE & POLL)

### 7.1 CRITICAL: CLIs Must STAY ALIVE

**CLIs do NOT exit when blocked. They STAY ALIVE and POLL.**

When a CLI encounters a blocker:
1. Log: "BLOCKED - waiting for {dependency}"
2. **STAY ALIVE** - Do not exit
3. **POLL** `project_state.json` every **60 seconds**
4. When dependency shows `DONE` → auto-unblock and proceed

### 7.2 Polling Protocol (MANDATORY)

```
BLOCKED CLI Behavior (STAY ALIVE):

LOOP:
  1. Read project_state.json
  2. Check dependency status
  3. If dependency DONE:
       → Change own status to IN_PROGRESS
       → Start work immediately
       → EXIT LOOP
  4. If dependency NOT DONE:
       → Log: "Still waiting... checking again in 60s"
       → WAIT 60 seconds
       → GOTO step 1

NEVER EXIT while blocked. ALWAYS POLL.
```

### 7.3 Poll Interval

| Situation | Poll Interval |
|-----------|---------------|
| BLOCKED waiting for dependency | 60 seconds |
| Between tasks | 30 seconds |
| After completing work | 60 seconds (check for new tasks) |

### 7.4 Stay Alive Rules

- **DO NOT** exit when blocked
- **DO NOT** exit after completing a task
- **ALWAYS** check for new work after completion
- **ALWAYS** poll state file periodically
- **ONLY** exit on explicit shutdown command or fatal error

### 7.5 Deadlock Prevention

If a CLI remains `BLOCKED` for more than **30 minutes**:

1. Log the block reason with timestamp
2. Update `project_state.json` with block details
3. Log: "DEADLOCK WARNING - blocked for 30+ minutes"
4. **CONTINUE POLLING** - do not exit
5. Claude Desktop will investigate and resolve

### 7.6 Example CLI Loop

```
CLI starts:
  → Read claude.md
  → Read project_state.json
  → Check own status

  IF status == BLOCKED:
    WHILE dependency not DONE:
      → Log "Waiting for {dependency}..."
      → Sleep 60 seconds
      → Re-read project_state.json
    END WHILE
    → Dependency satisfied, proceed to work

  IF status == TODO or IN_PROGRESS:
    → Do assigned work
    → Update state to DONE
    → Check for more work (poll)

  NEVER EXIT - always loop back and check for work
```

---

## 8. OWNERSHIP & WRITE BOUNDARIES

### 8.1 Ownership Rules

| CLI | May WRITE to | May READ |
|-----|--------------|----------|
| CLI 1 | `src/config/`, `src/processors/`, `src/orchestrator/`, `/docs/contracts/` | Everything |
| CLI 2 | `src/scrapers/` | Everything |
| CLI 3 | `src/notifiers/` | Everything |
| CLI 4 | `/testing/` | Everything |

### 8.2 Cross-Module Rules

- **NO CLI may overwrite another CLI's work**
- Cross-module refactors require Claude Desktop approval
- Shared utilities go in `src/` root (CLI 1 only)

---

## 9. TESTING & DEBUGGING (MANDATORY)

### 9.1 Testing Philosophy

**Testing is AUTOMATED and AUTONOMOUS.**

CLI 4 must be able to:
* Run all tests independently without human intervention
* Generate issue files for failures automatically
* Update logs with test results
* Re-run tests after fixes
* Validate fixes automatically

### 9.2 Test Plan Requirements

* A **test plan must exist** before implementation (`testing/test_plan.md`)
* Every feature requires:
  * Positive test (happy path)
  * Negative test (error conditions)
  * Edge case test (boundary conditions)
  * Integration test (component interactions)

### 9.3 Test Layers

| Layer | Duration | Trigger | Purpose |
|-------|----------|---------|---------|
| Unit | 30s | Every change | Component isolation |
| Integration | 5min | On completion | Component interaction |
| E2E | 30min | Daily | Full workflow |
| Health | Always | Scheduled | External API checks |

### 9.4 Mock vs Real

**Default: MOCK EVERYTHING**

- Never hit real websites during testing
- Mock all external APIs
- Use fixtures for reproducibility

### 9.5 Automated Issue Generation

When tests fail, CLI 4 creates:

```
testing/issues/issue_YYYYMMDD_HHMMSS.md
```

Contents:
- Error description
- Stack trace
- Failed component
- Reproduction steps
- Suggested fixes
- Priority (HIGH/MEDIUM/LOW)

**Other CLIs can pick up and fix these issues.**

### 9.6 CLI 4 Authority

- **CAN BLOCK** merges on test failures
- **NO CLI** may bypass failing tests
- **NO** temporary skips allowed
- **ALL** fixes must include tests

---

## 10. UNIFIED LOGGING STANDARD

### 10.1 Log Format

All CLIs must use this format:

```
[YYYY-MM-DD HH:MM:SS] [CLI_NAME] [PHASE] [ACTION] [RESULT]
Files: file1.py, file2.py
Details: Additional context here
---
```

### 10.2 Log Locations

| Log | Purpose |
|-----|---------|
| `/logs/cli_1.log` | CLI 1 activities |
| `/logs/cli_2.log` | CLI 2 activities |
| `/logs/cli_3.log` | CLI 3 activities |
| `/logs/cli_4.log` | CLI 4 test results |
| `/logs/phase_XX.log` | Phase summaries |
| `/logs/debug_summary.log` | Issue tracking |

---

## 11. CLAUDE DESKTOP AUTHORITY

### 11.1 Claude Desktop Role

Claude Desktop is the **SINGLE COMMAND AUTHORITY**:

- Issues all instructions
- Resolves conflicts between CLIs
- Approves architecture changes
- Updates task lists and priorities
- Unblocks stuck CLIs

### 11.2 Other CLI Behavior

Other CLIs (1-4):
- **MUST NOT** negotiate among themselves
- **MUST** re-read instructions at phase boundaries
- **MUST** obey waiting and dependency rules
- **MUST NOT** reinterpret rules
- **MUST NOT** ask questions unless explicitly permitted

---

## 12. MID-EXECUTION UPDATE HANDLING

### 12.1 Update Detection

If `claude.md` or `project_state.json` changes during execution:

1. CLI must stop at safe boundary
2. Re-read updated documents
3. Validate current work is still valid
4. Resume only if still aligned

### 12.2 Safe Boundaries

- After completing a function
- After completing a file
- After completing a test
- **NEVER** mid-function or mid-file

---

## 13. DEVELOPMENT RULES

### 13.1 Phase-Based Execution

All development follows **phase-based execution**:

1. Have a clear objective (from state file)
2. Be logged
3. Be tested
4. Be closed before next phase starts

### 13.2 Code Standards

- Prefer clarity over cleverness
- Avoid premature optimization
- Follow industry-standard patterns
- Keep files small and single-purpose
- Document decisions, not obvious code

---

## 14. FAILURE HANDLING

If something breaks:

1. **STOP** immediately
2. **LOG** the failure
3. **CREATE** issue file (if CLI 4) or **REPORT** (if other CLI)
4. **UPDATE** state to `FAILED`
5. **WAIT** for resolution

No step may be skipped. No silent fixes.

---

## 15. CONTRACTS & INTERFACES

### 15.1 Contract Location

```
/docs/contracts/
```

### 15.2 Contract Rules

- CLI 1 **defines** core contracts
- Other CLIs **consume** contracts exactly as defined
- No reinterpretation
- No duplication
- Changes require Claude Desktop approval

---

## 16. FINAL RULES

### 16.1 Execution Hierarchy

```
claude.md (this file)
    ↓
project_state.json
    ↓
contracts/*.md
    ↓
Individual CLI instructions
```

### 16.2 Core Principles

1. **READ** instructions before acting
2. **CHECK** state before proceeding
3. **LOG** everything
4. **TEST** everything
5. **UPDATE** state after completion

### 16.3 Forbidden Actions

🚫 No assumptions
🚫 No shortcuts
🚫 No drift from instructions
🚫 No silent decisions
🚫 No bypassing tests
🚫 No overwriting other CLI's work
🚫 No infinite waits

---

## 17. CLI QUICK START

### For CLI 1 (Core Builder):
```
1. Read /docs/project_state.json
2. If status is TODO → proceed
3. Build: config/, processors/, orchestrator/
4. Publish contracts to /docs/contracts/
5. Update state to DONE
6. Log to /logs/cli_1.log
```

### For CLI 2 (Scraper Builder):
```
1. Read /docs/project_state.json
2. Check CLI 1 config/ status
3. If DONE → proceed | If not → mark BLOCKED and stop
4. Build: all scrapers
5. Update state to DONE
6. Log to /logs/cli_2.log
```

### For CLI 3 (Notifier Builder):
```
1. Read /docs/project_state.json
2. Check CLI 1 config/ status
3. If DONE → proceed | If not → mark BLOCKED and stop
4. Build: all notifiers
5. Update state to DONE
6. Log to /logs/cli_3.log
```

### For CLI 4 (Test Runner):
```
1. Read /docs/project_state.json
2. Run all available tests
3. Generate issues for failures
4. Update state with results
5. Log to /logs/cli_4.log
```

---

**END OF GOVERNANCE DOCUMENT**

*Version: 2.0 | Multi-CLI Support | January 2026*
