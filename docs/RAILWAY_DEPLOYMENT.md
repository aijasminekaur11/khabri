# Railway.app Deployment Guide

## Quick Fix for "Context Canceled" Error

### The error you're seeing means Railway needs environment variables BEFORE building.

### Immediate Steps:

1. **Add Environment Variables in Railway Dashboard**
   - Go to your Railway project dashboard
   - Click "Variables" tab
   - Add ALL these variables (use your actual values from .env file):

```
TELEGRAM_BOT_TOKEN=<your_bot_token_from_dotenv>
TELEGRAM_CHAT_ID=5118231822,8259521446
TELEGRAM_AUTHORIZED_IDS=5118231822,8259521446
GH_TOKEN=<your_github_token_from_dotenv>
ANTHROPIC_API_KEY=<your_claude_api_key_from_dotenv>
GMAIL_ADDRESS=ai.jasminekaur11@gmail.com
GMAIL_APP_PASSWORD=<your_gmail_app_password_from_dotenv>
GITHUB_REPO=aijasminekaur11/khabri
```

2. **How to Get Values:**
   - Open your local .env file
   - Copy each value exactly
   - Paste into Railway Variables

3. **Trigger Redeploy:**
   - After adding ALL variables
   - Click "Redeploy" button in Railway
   - OR push any change to GitHub (auto-deploys)

4. **Check Logs:**
   - Go to "Logs" tab in Railway
   - Monitor build progress
   - Should complete in 2-3 minutes
   - Look for "Bot is now running" message

### What Fixed:
- Added railway.toml configuration
- Added Procfile for process definition
- Railway now knows how to run the bot

### After Deployment:
Test by sending /help to @Khabri420_bot on Telegram
