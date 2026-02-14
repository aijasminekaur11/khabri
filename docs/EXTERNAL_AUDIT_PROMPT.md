# EXTERNAL SECURITY & TECHNICAL AUDIT - KHABRI NEWS INTELLIGENCE SYSTEM

## AUDIT REQUEST DOCUMENT

**Project Name:** Khabri - News Intelligence System  
**Repository:** https://github.com/aijasminekaur11/khabri  
**Audit Type:** Comprehensive Technical & Security Audit  
**Requested Date:** February 2026  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Khabri is an automated News Intelligence System designed for content writers at Magic Bricks to:
- Monitor 18+ news sources for real estate, infrastructure, and policy news
- Track 326+ celebrities for property deals and investments
- Send automated digests at 7:00 AM and 4:00 PM IST
- Provide real-time alerts during special events (Budget, RBI Policy)
- Auto-fix issues via Telegram bot and Claude AI integration

### 1.2 System Architecture
- **Language:** Python 3.9+
- **Platform:** GitHub Actions + Railway/Heroku (optional)
- **Notifications:** Telegram Bot + Email (SMTP)
- **AI Integration:** Claude API (Anthropic) + Kimi API (Moonshot)
- **Data Storage:** YAML configs, GitHub cache, local filesystem
- **External APIs:** Telegram Bot API, GitHub API, News Sources (RSS/Scraping)

### 1.3 Scope of Audit
We require a comprehensive audit covering:
1. **Security Audit** (Secrets, API keys, data handling)
2. **Code Quality Audit** (Architecture, maintainability, bugs)
3. **Performance Audit** (Efficiency, resource usage, scalability)
4. **Compliance Audit** (GDPR, data privacy, terms of service)
5. **Infrastructure Audit** (CI/CD, deployment, monitoring)

---

## 2. SECURITY AUDIT REQUIREMENTS

### 2.1 Secrets & API Key Management
**Priority: CRITICAL**

Please audit the following:

#### API Keys & Tokens Used (REDACTED FOR AUDIT):
```yaml
# Telegram
TELEGRAM_BOT_TOKEN: [REDACTED - Telegram Bot Token]
TELEGRAM_CHAT_ID: [REDACTED - Chat IDs]

# GitHub
GH_TOKEN: [REDACTED - GitHub Personal Access Token]

# AI Services
ANTHROPIC_API_KEY: [REDACTED - Claude API Key]
KIMI_API_KEY: [REDACTED - Kimi/Moonshot API Key]
GOOGLE_API_KEY: [REDACTED - Google API Key]

# Email
EMAIL_PASSWORD: [REDACTED - Gmail App Password]
```

**Note:** Actual secrets will be provided securely to the audit agency via encrypted channel.

#### Audit Requirements:
1. **Secret Storage Analysis**
   - Are secrets hardcoded in the repository? (Check `.env`, `config/`, source files)
   - Are secrets committed to git history?
   - Review `.env.example` for accidental real credentials
   - Check if `.env` is properly in `.gitignore`

2. **Secret Rotation & Lifecycle**
   - Are API keys rotated regularly?
   - Do any keys have excessive permissions?
   - Are there any exposed keys in commit history?

3. **GitHub Actions Security**
   - Review `.github/workflows/*.yml` for secret usage
   - Check if `secrets.*` is used properly vs hardcoded values
   - Audit workflow permissions (check `permissions:` blocks)
   - Review for potential command injection vulnerabilities

4. **Telegram Bot Security**
   - Is bot token exposed anywhere?
   - Are chat IDs properly secured?
   - Is there authorization check for bot commands?

### 2.2 Data Privacy & GDPR Compliance
**Priority: HIGH**

#### Data Handled:
- User chat IDs (Telegram)
- Email addresses
- News article content (scraped)
- User preferences (keywords, celebrities)
- GitHub issue data

#### Audit Requirements:
1. **Data Collection Consent**
   - Is there a privacy policy?
   - Are users informed about data collection?
   - Is consent obtained for storing chat IDs/emails?

2. **Data Retention**
   - How long is user data retained?
   - Is there a data deletion mechanism?
   - Review `retention_days: 30` in config

3. **Data Processing**
   - Is PII (Personally Identifiable Information) encrypted at rest?
   - Are logs sanitized to remove sensitive data?
   - Check logging statements for accidental PII exposure

4. **Third-Party Data Sharing**
   - Are user chat IDs sent to AI services (Claude/Kimi)?
   - Is scraped news content processed by external AI?
   - Review data flow to external APIs

### 2.3 Web Scraping Compliance
**Priority: HIGH**

#### Audit Requirements:
1. **robots.txt Compliance**
   - Does the scraper respect robots.txt?
   - Check each source in `config/sources.yaml`

2. **Terms of Service**
   - Are scraped sources aware of automated access?
   - Rate limiting compliance (check `frequency_minutes` settings)

3. **Copyright & Fair Use**
   - Is scraped content properly attributed?
   - Are full articles stored or just summaries?
   - Check `summarizer.py` for content transformation

---

## 3. CODE QUALITY AUDIT

### 3.1 Architecture Review
**Priority: HIGH**

#### Project Structure:
```
src/
├── config/          # Configuration management
├── filters/         # News filtering
├── notifiers/       # Telegram, Email, AI
├── orchestrator/    # Main workflow
├── processors/      # Article processing
├── scrapers/        # Web scraping
└── scheduler/       # Timezone handling
```

#### Audit Requirements:
1. **Separation of Concerns**
   - Is each module properly isolated?
   - Check for circular dependencies
   - Review import patterns

2. **Error Handling**
   - Are exceptions properly caught and logged?
   - Is there graceful degradation?
   - Check for bare `except:` clauses

3. **Configuration Management**
   - Is configuration centralized?
   - Are defaults sensible?
   - Check `config_manager.py` implementation

4. **Logging Strategy**
   - Is logging consistent across modules?
   - Are sensitive values excluded from logs?
   - Review log rotation and retention

### 3.2 Code Review - Critical Files
**Priority: CRITICAL**

Please perform detailed code review of:

#### 3.2.1 Security-Critical Files:
1. `src/notifiers/telegram_bot_handler.py` (Bot commands, GitHub API)
2. `src/notifiers/claude_auto_fixer.py` (AI API integration)
3. `src/scrapers/*.py` (Web scraping, data extraction)
4. `scripts/auto_fix_with_claude.py` (Auto-fix logic)

#### 3.2.2 Business Logic Files:
1. `src/orchestrator/orchestrator.py` (Main workflow)
2. `src/processors/processor_pipeline.py` (Article processing)
3. `main.py` (Entry point, scheduling)

#### Audit Requirements:
1. **Input Validation**
   - Are user inputs (Telegram commands) validated?
   - Is there protection against injection attacks?
   - Check `/fix` command handler

2. **Path Traversal Protection**
   - Check file operations in `auto_fix_with_claude.py`
   - Review `_is_safe_path()` function
   - Check for directory traversal vulnerabilities

3. **Command Injection**
   - Review subprocess calls
   - Check shell command construction
   - Audit `run_tests()` function

4. **Race Conditions**
   - Check concurrent access to shared resources
   - Review file writing in auto-fix script
   - Check cache management

### 3.3 Bug Analysis
**Priority: MEDIUM**

#### Known Issues to Verify:
1. **Timezone Issues** (Historical problem)
   - Verify IST handling in `main.py`
   - Check `timezone_scheduler.py`
   - Review cron expressions in workflows

2. **Duplicate Prevention**
   - Check `deduplicator.py` implementation
   - Verify `last_morning_digest` tracking
   - Review cache invalidation

3. **API Rate Limiting**
   - Check if Claude/Kimi API calls are throttled
   - Verify Telegram rate limit handling
   - Review retry logic

---

## 4. PERFORMANCE AUDIT

### 4.1 Resource Usage
**Priority: MEDIUM**

#### Audit Requirements:
1. **Memory Usage**
   - Are large datasets held in memory?
   - Check article storage patterns
   - Review RSS feed parsing

2. **API Call Efficiency**
   - Are APIs called unnecessarily?
   - Check caching strategy
   - Review `frequency_minutes` settings

3. **GitHub Actions Usage**
   - Are workflows efficient?
   - Check for redundant runs
   - Review caching strategy

### 4.2 Scalability Assessment
**Priority: MEDIUM**

1. **Source Scaling**
   - Can the system handle 50+ news sources?
   - Review concurrent scraping design
   - Check for bottlenecks

2. **Celebrity Scaling**
   - Current: 326 celebrities
   - Can it handle 1000+ celebrities?
   - Check matching algorithm efficiency

3. **Notification Scaling**
   - Current: 2 chat IDs
   - Can it handle 100+ subscribers?
   - Review batching strategy

---

## 5. COMPLIANCE AUDIT

### 5.1 Legal Compliance
**Priority: HIGH**

1. **Copyright Compliance**
   - News content scraping legality
   - Summarization fair use doctrine
   - Attribution requirements

2. **Data Protection Laws**
   - India's DPDP Act 2023 compliance
   - GDPR compliance (if EU users)
   - Telegram data handling

3. **API Terms of Service**
   - Claude API usage compliance
   - Kimi API usage compliance
   - Telegram Bot API compliance
   - GitHub API rate limits

### 5.2 Accessibility & Ethics
**Priority: MEDIUM**

1. **Content Filtering**
   - Are inappropriate articles filtered?
   - Check keyword filtering
   - Review content moderation

2. **Bias Detection**
   - Is there bias in source selection?
   - Check for balanced news coverage
   - Review AI prompt engineering

---

## 6. INFRASTRUCTURE AUDIT

### 6.1 CI/CD Security
**Priority: HIGH**

#### GitHub Workflows:
1. `.github/workflows/scheduled-digest.yml`
2. `.github/workflows/auto-fix-issues.yml`
3. `.github/workflows/realtime-alerts.yml`
4. `.github/workflows/budget-event.yml`
5. `.github/workflows/rbi-policy-event.yml`

#### Audit Requirements:
1. **Workflow Security**
   - Check `permissions:` blocks
   - Review `secrets` usage
   - Check for `pull_request_target` risks

2. **Supply Chain Security**
   - Are actions pinned to specific versions?
   - Check for deprecated actions
   - Review third-party action trust

3. **Credential Exposure**
   - Check workflow logs for secret leakage
   - Review debug outputs
   - Check artifact handling

### 6.2 Deployment Security
**Priority: MEDIUM**

1. **Railway/Heroku Deployment**
   - Review `Procfile` and `railway.toml`
   - Check environment variable handling
   - Review restart policies

2. **Container Security** (if applicable)
   - Base image vulnerabilities
   - Dependency scanning
   - Runtime security

---

## 7. DELIVERABLES REQUIRED

### 7.1 Security Audit Report
Must include:
1. **Executive Summary** (Non-technical, 1 page)
2. **Critical Vulnerabilities** (CVSS scoring)
3. **High/Medium/Low Issues** (Categorized)
4. **Secret Exposure Analysis** (Detailed list)
5. **Remediation Plan** (Prioritized actions)

### 7.2 Code Quality Report
Must include:
1. **Architecture Assessment** (Diagrams + analysis)
2. **Code Review Findings** (Per critical file)
3. **Bug List** (With severity and fix suggestions)
4. **Technical Debt Assessment**
5. **Refactoring Recommendations**

### 7.3 Compliance Report
Must include:
1. **Legal Risk Assessment**
2. **Privacy Compliance Checklist**
3. **Terms of Service Compliance**
4. **Recommended Legal Disclaimers**

### 7.4 Performance Report
Must include:
1. **Bottleneck Analysis**
2. **Scalability Projections**
3. **Resource Usage Analysis**
4. **Optimization Recommendations**

---

## 8. AUDIT TIMELINE

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Initial Assessment | 2 days | High-level findings |
| Security Deep Dive | 5 days | Security report |
| Code Review | 5 days | Code quality report |
| Compliance Review | 3 days | Compliance report |
| Final Report | 2 days | Comprehensive document |
| **Total** | **17 days** | All deliverables |

---

## 9. ACCESS REQUIREMENTS

We will provide:
1. GitHub repository access (read-only)
2. Environment variable list (redacted)
3. Architecture documentation
4. API documentation
5. Sample workflow runs

---

## 10. ACCEPTANCE CRITERIA

The audit will be considered complete when:
1. All CRITICAL and HIGH security issues are documented
2. Secret exposure analysis is complete
3. Remediation plan is actionable
4. Code quality score is provided
5. Compliance gaps are identified
6. Final presentation to stakeholders is delivered

---

## 11. CONFIDENTIALITY

This audit involves:
- Proprietary business logic
- API keys (will be rotated after audit)
- User data handling practices
- Competitive intelligence gathering methods

**All findings must be kept strictly confidential.**

---

## 12. CONTACT INFORMATION

**Project Owner:** Jasmine Kaur  
**Repository:** https://github.com/aijasminekaur11/khabri  
**Primary Use Case:** Content intelligence for Magic Bricks

---

**END OF AUDIT REQUEST**

