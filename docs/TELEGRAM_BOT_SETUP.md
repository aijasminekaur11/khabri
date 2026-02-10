# 🤖 Telegram Bot Setup Guide

This guide shows how to set up the Telegram bot that allows your wife to send fix requests from her mobile phone.

## 📱 How It Works

1. **Your wife sends a Telegram message**: `/fix Budget alerts not working`
2. **Bot creates a GitHub issue** with the description
3. **GitHub Actions automatically runs** and attempts to fix the issue
4. **Your wife gets notified** when the fix is ready via Telegram
5. **She reviews and merges** the pull request from her phone

---

## 🚀 Quick Start (Step-by-Step)

### Step 1: Create a Telegram Bot

1. **Open Telegram** on your phone
2. **Search for** `@BotFather` (official Telegram bot creator)
3. **Send** `/newbot` command
4. **Follow the prompts**:
   - Choose a name (e.g., "Khabri Assistant")
   - Choose a username (e.g., "khabri_fix_bot")
5. **Save the bot token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID

1. **Open your new bot** in Telegram
2. **Send any message** to the bot (e.g., "Hello")
3. **Open this URL** in your browser (replace `YOUR_BOT_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
4. **Find your chat ID** in the response (look for `"chat":{"id":123456789`)
5. **Save this number** (your chat ID)

### Step 3: Create GitHub Personal Access Token

1. **Go to GitHub Settings**: https://github.com/settings/tokens
2. **Click** "Generate new token (classic)"
3. **Give it a name**: "Telegram Bot Access"
4. **Select scopes**:
   - ✅ `repo` (full control of private repositories)
   - ✅ `workflow` (update GitHub Action workflows)
5. **Click** "Generate token"
6. **Copy and save the token** (you won't see it again!)

### Step 4: Add Secrets to GitHub Repository

1. **Go to your repository**: https://github.com/aijasminekaur11/khabri
2. **Click** Settings → Secrets and variables → Actions
3. **Add these repository secrets**:

   | Name | Value | Where to get it |
   |------|-------|----------------|
   | `TELEGRAM_BOT_TOKEN` | Your bot token from Step 1 | BotFather |
   | `TELEGRAM_CHAT_ID` | Your chat ID from Step 2 | getUpdates API |
   | `GH_TOKEN` | Your PAT from Step 3 | GitHub Settings |

### Step 5: Create Environment File (For Local Bot)

Create a file named `.env` in your project root:

```bash
# .env file
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
GH_TOKEN=ghp_your_github_token_here
GITHUB_REPO=aijasminekaur11/khabri
```

**⚠️ Important**: Add `.env` to your `.gitignore` (already done)

### Step 6: Install Dependencies

```bash
pip install python-telegram-bot requests PyGithub python-dotenv
```

### Step 7: Run the Bot Locally

```bash
python scripts/run_telegram_bot.py
```

You should see:
```
============================================================
🤖 TELEGRAM BOT - STARTING
============================================================

📋 Configuration:
   Repository: aijasminekaur11/khabri
   Bot Token: 1234567890...
   GitHub Token: ✅ SET

✅ Bot initialized successfully

============================================================
🚀 BOT IS NOW RUNNING
============================================================

Available commands for users:
   /fix <description> - Create automated fix request
   /status - Check recent fixes
   /help - Show help message

Press Ctrl+C to stop the bot
```

---

## 📱 Using the Bot (For Your Wife)

### Command 1: `/fix` - Create Fix Request

**Send this in Telegram:**
```
/fix Budget alerts showing wrong category news
```

**Bot responds:**
```
🔄 Creating fix request...
Please wait while I create a GitHub issue.
```

**Then:**
```
✅ Fix request created successfully!

📋 Issue: #123
🔗 Link: https://github.com/aijasminekaur11/khabri/issues/123

🤖 Claude Code will automatically:
1. Analyze the issue
2. Create a fix
3. Run tests
4. Create a pull request

You'll receive a notification when the fix is ready for review.
```

### Command 2: `/status` - Check Recent Fixes

**Send this in Telegram:**
```
/status
```

**Bot responds:**
```
📊 Recent Fix Requests

✅ #123 - Budget alerts showing wrong category news
   Status: Completed

🔄 #122 - Login page broken on mobile
   Status: PR Ready

⏳ #121 - Telegram notifications not sending
   Status: In Progress
```

### Command 3: `/help` - Get Help

**Send this in Telegram:**
```
/help
```

**Bot responds with full command list**

---

## 🔧 How the Auto-Fix Works

### Workflow Overview

```
1. User sends /fix command via Telegram
   ↓
2. Telegram bot creates GitHub Issue with 'auto-fix' label
   ↓
3. GitHub Actions workflow triggers automatically
   ↓
4. Workflow analyzes the issue description
   ↓
5. Workflow creates a fix branch
   ↓
6. Workflow applies automated fixes (placeholder for now)
   ↓
7. Workflow runs tests
   ↓
8. Workflow creates Pull Request
   ↓
9. User receives Telegram notification with PR link
   ↓
10. User reviews and merges PR from GitHub mobile app
```

### GitHub Actions Workflow

The workflow file `.github/workflows/auto-fix-issues.yml` handles:

- ✅ Validates issues with `auto-fix` label
- ✅ Creates fix branch automatically
- ✅ Runs tests to verify fixes
- ✅ Creates pull request
- ✅ Sends Telegram notification
- ✅ Updates issue with progress

---

## 🌐 Running Bot 24/7 (Production)

### Option 1: Run on Your Computer

**Pros**: Free, simple setup
**Cons**: Computer must stay on

```bash
# Run in background (Linux/Mac)
nohup python scripts/run_telegram_bot.py > bot.log 2>&1 &

# Run in background (Windows)
start /B python scripts\run_telegram_bot.py
```

### Option 2: Run on Cloud Server (Recommended)

**Use Railway, Heroku, or DigitalOcean**

1. **Create** a `Procfile`:
   ```
   worker: python scripts/run_telegram_bot.py
   ```

2. **Deploy** to your chosen platform
3. **Set environment variables** in platform dashboard
4. **Start** the worker process

### Option 3: Run as Systemd Service (Linux)

Create `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Bot for Khabri
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/News_Update
Environment="TELEGRAM_BOT_TOKEN=your-token"
Environment="GH_TOKEN=your-token"
Environment="GITHUB_REPO=aijasminekaur11/khabri"
ExecStart=/usr/bin/python3 scripts/run_telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

---

## 🧪 Testing the Setup

### Test 1: Send Help Command

1. Open Telegram
2. Find your bot
3. Send: `/help`
4. Verify you get help message

### Test 2: Create Test Fix Request

1. Send: `/fix This is a test fix request`
2. Verify bot responds with "Creating fix request..."
3. Check GitHub for new issue
4. Verify issue has `auto-fix` label
5. Check GitHub Actions tab for running workflow

### Test 3: Check Status

1. Send: `/status`
2. Verify you see recent issues

---

## 🔒 Security Best Practices

1. **Never commit** `.env` file to Git
2. **Use GitHub Secrets** for all tokens
3. **Restrict bot access** to specific chat IDs (optional)
4. **Review PRs** before merging (don't auto-merge)
5. **Monitor bot logs** for suspicious activity

### Optional: Restrict to Specific Users

Edit `src/notifiers/telegram_bot_handler.py`:

```python
ALLOWED_CHAT_IDS = [123456789, 987654321]  # Your and wife's chat IDs

def process_message(self, message: Dict[str, Any]) -> bool:
    chat_id = message['chat']['id']

    if chat_id not in ALLOWED_CHAT_IDS:
        self.send_message(
            chat_id,
            "❌ Unauthorized. This bot is private."
        )
        return False

    # Rest of processing...
```

---

## 🐛 Troubleshooting

### Bot Not Responding

**Check:**
1. Bot is running: `ps aux | grep run_telegram_bot`
2. Correct token in `.env` or environment
3. Internet connection
4. Bot logs: `tail -f logs/telegram_bot.log`

### GitHub Issues Not Created

**Check:**
1. `GH_TOKEN` has correct permissions
2. `GITHUB_REPO` is correctly formatted: `owner/repo`
3. Repository exists and token has access
4. GitHub API status: https://www.githubstatus.com/

### Workflow Not Triggering

**Check:**
1. Issue has `auto-fix` label
2. Workflow file exists: `.github/workflows/auto-fix-issues.yml`
3. GitHub Actions enabled in repository settings
4. Check Actions tab for errors

### Telegram Notifications Not Sent

**Check:**
1. `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in GitHub Secrets
2. Secrets are correctly named (case-sensitive)
3. Workflow completed successfully
4. Check workflow logs for errors

---

## 📚 Additional Resources

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **GitHub Actions**: https://docs.github.com/en/actions
- **GitHub API**: https://docs.github.com/en/rest

---

## 🎯 Example Usage Scenarios

### Scenario 1: Bug Report

**Wife sends:**
```
/fix Budget alerts are showing crypto news instead of real estate
```

**What happens:**
1. Issue created: "Budget alerts are showing crypto news instead of real estate"
2. GitHub Actions runs analysis
3. Creates PR with potential fix
4. Wife gets notification
5. Wife reviews PR on GitHub mobile
6. Wife merges if fix looks good

### Scenario 2: Feature Request

**Wife sends:**
```
/fix Add notifications for RBI policy changes
```

**What happens:**
1. Issue created with feature description
2. Workflow analyzes request
3. May require manual implementation
4. Developer gets notified
5. Feature implemented
6. Wife gets update when ready

### Scenario 3: Check Status

**Wife sends:**
```
/status
```

**Sees:**
```
📊 Recent Fix Requests

✅ #125 - Budget alerts fixed
✅ #124 - Telegram working again
🔄 #123 - RBI notifications (PR ready)
```

---

## 📝 Summary

✅ **Setup complete when:**
- Telegram bot created and token saved
- GitHub token created with correct permissions
- All secrets added to GitHub repository
- Bot running locally or on server
- Test `/fix` command works
- GitHub issue created automatically
- Telegram notification received

✅ **Your wife can now:**
- Send `/fix` commands from her phone anytime
- Check status with `/status`
- Get help with `/help`
- Receive notifications when fixes are ready
- Review and merge PRs from GitHub mobile app

---

**Need help?** Check the troubleshooting section or create a GitHub issue!
