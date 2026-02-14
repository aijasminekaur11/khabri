# Privacy Policy - Khabri News Intelligence System

**Effective Date:** February 2026  
**Last Updated:** February 14, 2026

---

## 1. INTRODUCTION

Khabri ("we," "our," or "us") is an automated News Intelligence System designed for content writers at Magic Bricks. This Privacy Policy explains how we collect, use, store, and protect your information when you use our services.

**By using Khabri, you agree to the collection and use of information in accordance with this policy.**

---

## 2. INFORMATION WE COLLECT

### 2.1 User-Provided Information
- **Telegram Chat IDs**: Used to send news digests and alerts
- **Email Addresses**: Used for email notifications (optional)
- **GitHub Account Information**: Used for issue creation and auto-fix features

### 2.2 Automatically Collected Information
- **News Articles**: Publicly available news content from configured sources
- **System Logs**: Error logs and performance metrics (anonymized)
- **Usage Patterns**: Frequency of digest delivery and alert triggers

### 2.3 We DO NOT Collect
- Passwords or authentication credentials (except API keys stored securely)
- Personal messages or private communications
- Financial information
- Location data beyond timezone preferences

---

## 3. HOW WE USE YOUR INFORMATION

### 3.1 Primary Purposes
- **Deliver News Digests**: Send scheduled morning (7:00 AM) and evening (4:00 PM) IST news summaries
- **Real-Time Alerts**: Notify about breaking news and competitor updates
- **Auto-Fix Issues**: Create GitHub issues and generate fixes via AI (Claude/Kimi)

### 3.2 AI Processing Disclosure
**IMPORTANT**: When you use the `/fix` command via Telegram:
- Your issue description is sent to **Anthropic (Claude API)** or **Moonshot (Kimi API)**
- Portions of the codebase may be shared with these AI services for context
- No Chat IDs, email addresses, or secrets are sent to AI services
- AI processing is necessary for auto-fix functionality

### 3.3 Legal Basis (GDPR/DPDP Compliance)
- **Consent**: By using the bot, you consent to data processing
- **Legitimate Interest**: News aggregation for content writing purposes
- **Contract**: Service delivery based on your configuration

---

## 4. DATA SHARING AND THIRD PARTIES

### 4.1 Third-Party Services We Use

| Service | Purpose | Data Shared |
|---------|---------|-------------|
| **Telegram Bot API** | Message delivery | Chat IDs, message content |
| **GitHub API** | Issue creation | Issue titles, descriptions |
| **Anthropic Claude** | AI analysis | Code snippets, issue descriptions |
| **Moonshot (Kimi)** | AI code generation | Code context, issue details |
| **News Sources** | Content scraping | Public news articles only |

### 4.2 We Do NOT Sell Your Data
We do not sell, trade, or rent your personal information to third parties.

### 4.3 Legal Disclosure
We may disclose information if required by:
- Court order or legal process
- Government request
- Protection of our rights or safety

---

## 5. DATA STORAGE AND SECURITY

### 5.1 Storage Locations
- **Configuration**: YAML files in private GitHub repository
- **Cache**: GitHub Actions cache (temporary, encrypted)
- **Logs**: Local/Railway server logs (7-day retention)

### 5.2 Security Measures
- API keys stored in environment variables (not in code)
- `.gitignore` prevents accidental secret commits
- GitHub secret scanning enabled
- Rate limiting on all external requests

### 5.3 Data Retention
- **News Articles**: 30 days (configurable)
- **Chat IDs**: Until service termination or deletion request
- **Logs**: 7 days
- **GitHub Issues**: Until manually closed/deleted

---

## 6. WEB SCRAPING AND COPYRIGHT

### 6.1 robots.txt Compliance
We respect `robots.txt` directives from all news sources:
- Check robots.txt before scraping
- Honor crawl-delay directives
- Stop scraping if disallowed

### 6.2 Fair Use
- Only article summaries and excerpts are stored
- Full articles are not reproduced
- Attribution to original sources is maintained
- News content is transformed (summarized, categorized)

### 6.3 Third-Party Terms
Users are responsible for ensuring:
- News source Terms of Service permit scraping
- Celebrity tracking complies with privacy laws
- Commercial use is permitted by content sources

---

## 7. YOUR RIGHTS

### 7.1 Access and Control
You can:
- Request a copy of your data
- Update your preferences (news categories, timing)
- Opt-out of specific notification channels
- Delete your data from our systems

### 7.2 GDPR Rights (EU Users)
- **Right to Access**: Request your personal data
- **Right to Rectification**: Correct inaccurate data
- **Right to Erasure**: Request data deletion
- **Right to Restrict Processing**: Limit data use
- **Right to Data Portability**: Export your data
- **Right to Object**: Opt-out of processing

### 7.3 DPDP Rights (Indian Users)
As per India's Digital Personal Data Protection Act 2023:
- Right to access personal data
- Right to correction and erasure
- Right to grievance redressal
- Right to nominate

---

## 8. AI AND AUTOMATED DECISION-MAKING

### 8.1 AI Usage
Our system uses AI for:
- News summarization
- Content categorization
- Celebrity name matching
- Code auto-fix generation

### 8.2 Human Oversight
- All auto-fixes require manual review before deployment
- News categorization can be manually corrected
- AI-generated summaries are marked as such

### 8.3 No Automated Profiling
We do not use AI to profile users or make decisions affecting legal rights.

---

## 9. CHILDREN'S PRIVACY

Khabri is not intended for use by individuals under 18 years of age. We do not knowingly collect personal information from children.

---

## 10. CHANGES TO THIS POLICY

We may update this Privacy Policy periodically. Changes will be:
- Posted in Telegram bot with /privacy command
- Updated in the GitHub repository
- Notified via email (if configured)

**Continued use after changes constitutes acceptance.**

---

## 11. CONTACT US

For privacy-related questions, data requests, or concerns:

**Project Owner:** Jasmine Kaur  
**Repository:** https://github.com/aijasminekaur11/khabri  
**Telegram Bot:** @KhabriNewsBot

**For Data Deletion Requests:**
Send `/delete_my_data` command to the Telegram bot or create a GitHub issue.

---

## 12. COMPLIANCE SUMMARY

| Regulation | Status | Notes |
|------------|--------|-------|
| **GDPR** | Compliant with noted disclosures | AI processing disclosed |
| **DPDP Act 2023 (India)** | Compliant | Data retention, user rights |
| **Telegram ToS** | Compliant | Bot API usage |
| **GitHub ToS** | Compliant | API and repository usage |
| **Copyright/Fair Use** | Best effort | robots.txt compliance, attribution |

---

**END OF PRIVACY POLICY**

