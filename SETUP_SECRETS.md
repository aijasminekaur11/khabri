# 🔐 Secret Keys Setup Guide

This guide shows you where to add your API keys for the auto-fix system.

## Overview

The auto-fix system now uses:
- **PRIMARY**: Google Gemini API (cheaper, faster)
- **BACKUP**: Anthropic Claude API (fallback if Gemini fails)

---

## 1️⃣ GitHub Secrets (for Auto-Fix Workflow)

### Steps to Add Secrets in GitHub:

1. Go to your repository: `https://github.com/aijasminekaur11/khabri`
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret** button

### Add These Secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `GEMINI_API_KEY` | Your Gemini API key | Primary AI for auto-fix |
| `ANTHROPIC_API_KEY` | Your Claude API key | Backup AI for auto-fix |
| `GH_TOKEN` | Your GitHub Personal Access Token | Already added ✅ |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Already added ✅ |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | Already added ✅ |

### Screenshot Reference:
```
GitHub Repo → Settings → Secrets and variables → Actions → New repository secret
```

---

## 2️⃣ Railway Environment Variables (for Main App)

### Steps to Add Environment Variables in Railway:

1. Go to Railway dashboard: `https://railway.app/dashboard`
2. Select your project: **Khabri** or **News_Update**
3. Click on your service/deployment
4. Click **Variables** tab
5. Click **+ New Variable** button

### Add These Variables:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `GEMINI_API_KEY` | Your Gemini API key | Primary AI service |
| `GOOGLE_API_KEY` | Your Gemini API key (same as above) | Alternative name |
| `ANTHROPIC_API_KEY` | Your Claude API key | Backup AI service |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Already added ✅ |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | Already added ✅ |
| `SMTP_*` | Your email settings | Already added ✅ |

**Note**: You can add both `GEMINI_API_KEY` and `GOOGLE_API_KEY` with the same value for compatibility.

### Screenshot Reference:
```
Railway Dashboard → Your Project → Service → Variables → + New Variable
```

---

## 3️⃣ Local .env File (for Testing Locally)

If you want to test the auto-fix locally, update your `.env` file:

```bash
# AI APIs
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here

# GitHub
GH_TOKEN=your_github_token_here
GITHUB_REPOSITORY=aijasminekaur11/khabri

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Email (existing)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

---

## 4️⃣ How to Get Gemini API Key

### Steps:

1. Go to: `https://aistudio.google.com/app/apikey`
2. Click **"Get API key"** or **"Create API key"**
3. Select a Google Cloud project (or create new one)
4. Copy the API key

**Note**: Gemini API has a free tier with generous limits!

### Pricing (as of 2025):
- **Free Tier**: 15 requests/minute, 1 million tokens/day
- **Paid**: Much cheaper than Claude

---

## 5️⃣ Verification Checklist

After adding all secrets, verify:

### GitHub Actions:
- [ ] Go to repo → Settings → Secrets and variables → Actions
- [ ] Confirm `GEMINI_API_KEY` is listed
- [ ] Confirm `ANTHROPIC_API_KEY` is listed (backup)
- [ ] Confirm `GH_TOKEN` is listed
- [ ] Confirm `TELEGRAM_BOT_TOKEN` is listed
- [ ] Confirm `TELEGRAM_CHAT_ID` is listed

### Railway:
- [ ] Go to Railway → Your project → Variables tab
- [ ] Confirm `GEMINI_API_KEY` or `GOOGLE_API_KEY` is listed
- [ ] Confirm `ANTHROPIC_API_KEY` is listed (backup)
- [ ] Confirm `TELEGRAM_BOT_TOKEN` is listed
- [ ] Confirm `TELEGRAM_CHAT_ID` is listed

---

## 6️⃣ How the Fallback System Works

When an auto-fix is triggered:

1. **Try Gemini first** (PRIMARY)
   - If successful → Use Gemini's response ✅
   - If fails → Go to step 2 ⚠️

2. **Try Claude** (BACKUP)
   - If successful → Use Claude's response ✅
   - If fails → Report both errors ❌

### Logs will show:
```
[PRIMARY] Trying Gemini API...
✅ Success!
```

Or if Gemini fails:
```
[PRIMARY] Trying Gemini API...
[PRIMARY FAILED] Gemini error: API key invalid
[BACKUP] Falling back to Claude API...
✅ Success!
```

---

## 7️⃣ Testing the Auto-Fix

After adding secrets, test the system:

1. Create a test issue on GitHub with title: `[Auto-Fix] Test notification`
2. Check GitHub Actions → Workflows → Should see "Auto-Fix via Telegram" running
3. Check Telegram → Should receive notification
4. Check the logs to see if Gemini or Claude was used

---

## 8️⃣ Troubleshooting

### Issue: "GEMINI_API_KEY not found"
**Solution**:
- Check GitHub Secrets (for auto-fix workflow)
- Check Railway Variables (for main app)
- Make sure spelling is exact: `GEMINI_API_KEY`

### Issue: "Both AI providers failed"
**Solution**:
- Verify both API keys are valid
- Check API quotas/limits
- Check logs for specific error messages

### Issue: Auto-fix still failing
**Solution**:
- Go to GitHub → Actions → Click on failed workflow
- Read the logs to see exact error
- Most likely: API key not added or invalid

---

## 9️⃣ Cost Savings

By switching to Gemini as primary:

| Provider | Cost (per 1M tokens) | Speed |
|----------|---------------------|-------|
| **Gemini 2.0 Flash** | $0.075 - $0.30 | Fast ⚡ |
| Claude Sonnet 4.5 | $3 - $15 | Medium 🐌 |

**Estimated savings: 90%+ on auto-fix costs!**

---

## 🎯 Quick Summary

**You need to add `GEMINI_API_KEY` in 2 places:**

1. **GitHub Repository Secrets** (for auto-fix workflow)
   - Go to: `https://github.com/aijasminekaur11/khabri/settings/secrets/actions`
   - Add: `GEMINI_API_KEY`

2. **Railway Environment Variables** (for main app)
   - Go to Railway dashboard → Your project → Variables
   - Add: `GEMINI_API_KEY` or `GOOGLE_API_KEY`

**Backup**: Keep `ANTHROPIC_API_KEY` in both places as backup.

---

## ✅ Done!

After adding the keys:
1. Push these code changes to GitHub
2. Wait for GitHub Actions to rebuild
3. Trigger a new auto-fix with `/fix` command
4. Check if it uses Gemini (should see in logs)

**Good luck! 🚀**
