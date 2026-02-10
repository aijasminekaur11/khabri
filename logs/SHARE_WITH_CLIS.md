# 🚀 PHASE 05B: PARALLEL EXECUTION - CLI COMMANDS

## 📋 COMMANDS TO SHARE WITH EACH CLI

---

## 🔵 CLI 1: Coverage Improvement Squad

**Copy and share this with CLI 1:**

```
You are CLI 1 - Coverage Improvement Squad.

READ: D:\Jasmine\00001_Content_app\News_Update\logs\cli_1_commands.txt

MISSION: Increase test coverage from 82.47% to 90%+

PRIMARY TASK: Expand testing/test_cases/unit/test_news_scraper.py
- Add 50-60 comprehensive test cases
- Cover: Economic Times, Livemint, Housing.com scrapers
- Test: Error handling, edge cases, rate limiting
- Target: News Scraper 21% → 90%

SECONDARY TASK: Fill config module gaps
- Add 15-20 tests for config_validator.py
- Add 10-15 tests for config_manager.py

VERIFICATION:
cd D:\Jasmine\00001_Content_app\News_Update
python -m pytest testing/test_cases/ --cov=src --cov-report=term-missing

GOAL: Achieve 90%+ overall coverage

START NOW: Begin adding comprehensive test cases.
```

---

## 🟢 CLI 2: Integration Engineer

**Copy and share this with CLI 2:**

```
You are CLI 2 - Integration Engineer.

READ: D:\Jasmine\00001_Content_app\News_Update\logs\cli_2_commands.txt

MISSION: Begin PHASE_06 Integration work

PRIMARY TASKS:
1. Component Orchestration Tests
   - Config Manager → Scrapers → Processors → Notifiers

2. Data Flow Validation
   - Morning digest workflow
   - Real-time alert workflow
   - Event-triggered scraping

3. Real Config Integration
   - Test with sample sources.json
   - Test with sample keywords.json
   - Validate full pipeline

4. System Stability Tests
   - Concurrent scraper execution
   - Memory usage under load
   - Error propagation
   - Graceful degradation

CREATE: 20-30 new integration tests in testing/test_cases/integration/

VERIFICATION:
cd D:\Jasmine\00001_Content_app\News_Update
python -m pytest testing/test_cases/integration/ -v

GOAL: Validate all component interactions

START NOW: Begin creating integration test suite.
```

---

## 🟡 CLI 3: Communication Tester

**Copy and share this with CLI 3:**

```
You are CLI 3 - Communication Tester.

READ: D:\Jasmine\00001_Content_app\News_Update\logs\cli_3_commands.txt

MISSION: Test Email + Telegram with REAL .env credentials

TELEGRAM TESTS (4 tests):
1. Send Simple Message
2. Send Formatted Alert
3. Send Digest
4. Error Handling

Run each test:
cd D:\Jasmine\00001_Content_app\News_Update

Test 1 - Simple Message:
python -c "from src.notifiers.telegram_notifier import TelegramNotifier; import asyncio; asyncio.run(TelegramNotifier().send_message('✅ Telegram Test'))"

Test 2 - Alert:
python -c "from src.notifiers.telegram_notifier import TelegramNotifier; import asyncio; asyncio.run(TelegramNotifier().send_alert({'title': 'Test', 'summary': 'Test summary', 'priority': 8}))"

EMAIL TESTS (4 tests):
1. Send Simple Email
2. Send Formatted Alert
3. Send Morning Digest
4. Error Handling

Test 1 - Simple Email:
python -c "from src.notifiers.email_notifier import EmailNotifier; import asyncio; asyncio.run(EmailNotifier().send_email('Test Subject', 'Test Body'))"

DOCUMENTATION: Create testing/reports/communication_test_report.md

GOAL:
✅ At least 1 successful Telegram message
✅ At least 1 successful Email delivery
✅ Report with results

START NOW: Begin testing with real credentials.
```

---

## 🔴 CLI 4: Test Runner & Monitor

**Copy and share this with CLI 4:**

```
You are CLI 4 - Test Runner & Monitor.

READ: D:\Jasmine\00001_Content_app\News_Update\logs\cli_4_commands.txt

MISSION: Monitor all 3 CLIs and re-run tests as needed

MONITORING PROTOCOL (Every 60 seconds):
1. Read project_state.json for updates
2. If CLI 1 updated → Run full test suite with coverage
3. If CLI 2 updated → Run integration tests
4. If CLI 3 updated → Check communication results
5. Update test results in project_state.json
6. Log to logs/cli_4.log
7. Sleep 60 seconds
8. Repeat

MAIN COMMAND:
cd D:\Jasmine\00001_Content_app\News_Update
python -m pytest testing/test_cases/ --cov=src --cov-report=term-missing --cov-report=html -v

TRACK:
- Coverage: Current 82.47% → Target 90%+
- CLI 1: Test additions, coverage increase
- CLI 2: Integration test additions
- CLI 3: Communication test results

REPORT: After each test run to logs/cli_4.log and project_state.json

GOAL: Monitor progress, ensure all tests pass, report status

START NOW: Begin monitoring loop.
```

---

## 📂 FILE LOCATIONS

All command files available at:
- `D:\Jasmine\00001_Content_app\News_Update\logs\cli_1_commands.txt`
- `D:\Jasmine\00001_Content_app\News_Update\logs\cli_2_commands.txt`
- `D:\Jasmine\00001_Content_app\News_Update\logs\cli_3_commands.txt`
- `D:\Jasmine\00001_Content_app\News_Update\logs\cli_4_commands.txt`

---

## 🚀 EXECUTION ORDER

**ALL 3 CLIs CAN START IN PARALLEL:**

1. Open 4 separate Claude Code instances
2. Assign each instance a CLI role (1, 2, 3, or 4)
3. Copy the command text from above
4. Paste into the Claude Code instance
5. CLI will read its detailed instructions and begin work

**OR Use these commands:**

```bash
# CLI 1
cat D:\Jasmine\00001_Content_app\News_Update\logs\cli_1_commands.txt

# CLI 2
cat D:\Jasmine\00001_Content_app\News_Update\logs\cli_2_commands.txt

# CLI 3
cat D:\Jasmine\00001_Content_app\News_Update\logs\cli_3_commands.txt

# CLI 4
cat D:\Jasmine\00001_Content_app\News_Update\logs\cli_4_commands.txt
```

---

## ✅ READY TO LAUNCH

**Share the appropriate command block with each CLI and they will begin work autonomously!**

---

*Generated by: CLAUDE_DESKTOP Orchestrator*
*Date: 2026-01-31T02:00:00Z*
*Phase: PHASE_05B_PARALLEL_WORK*
