# 🤖 Telegram Bot for Auto-Fix Requests

**Allow your wife to request fixes from her mobile phone via Telegram!**

---

## 🎯 Quick Overview

This Telegram bot integration allows anyone to:
1. Send `/fix` commands via Telegram
2. Automatically creates GitHub issues
3. Triggers automated fixes via GitHub Actions
4. Sends notifications when fixes are ready
5. Review and merge fixes from mobile

---

## 📚 Documentation

- **[Setup Guide](docs/TELEGRAM_BOT_SETUP.md)** - Complete setup instructions
- **[User Guide](docs/TELEGRAM_BOT_USER_GUIDE.md)** - Simple guide for your wife

---

## ⚡ Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-telegram-bot.txt
```

### 2. Set Up Environment Variables

Create a `.env` file:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
GH_TOKEN=your_github_token_here
GITHUB_REPO=aijasminekaur11/khabri
```

### 3. Run the Bot

```bash
python scripts/run_telegram_bot.py
```

---

## 📱 Usage Examples

### Request a Fix
```
/fix Budget alerts showing wrong news category
```

### Check Status
```
/status
```

### Get Help
```
/help
```

---

## 🏗️ Architecture

```
Telegram User
    ↓ (sends /fix command)
Telegram Bot Handler
    ↓ (creates issue)
GitHub Issue (with auto-fix label)
    ↓ (triggers)
GitHub Actions Workflow
    ↓ (analyzes & fixes)
Pull Request
    ↓ (notifies)
Telegram User (gets notification)
```

---

## 📂 Files Created

### Core Bot
- `src/notifiers/telegram_bot_handler.py` - Main bot logic
- `scripts/run_telegram_bot.py` - Bot runner script

### GitHub Actions
- `.github/workflows/auto-fix-issues.yml` - Auto-fix workflow

### Documentation
- `docs/TELEGRAM_BOT_SETUP.md` - Technical setup guide
- `docs/TELEGRAM_BOT_USER_GUIDE.md` - User-friendly guide
- `requirements-telegram-bot.txt` - Python dependencies

---

## 🔑 Required Secrets

Add these to GitHub repository secrets:

| Secret Name | Description |
|-------------|-------------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `GH_TOKEN` | Personal access token |

---

## ✅ Features

- ✅ `/fix` - Create automated fix requests
- ✅ `/status` - Check recent fixes
- ✅ `/help` - Show available commands
- ✅ Automatic GitHub issue creation
- ✅ GitHub Actions integration
- ✅ Telegram notifications
- ✅ Pull request auto-creation
- ✅ Mobile-friendly workflow

---

## 🚀 Deployment Options

### Option 1: Local Machine
```bash
python scripts/run_telegram_bot.py
```

### Option 2: Cloud Server
Deploy to Railway, Heroku, or DigitalOcean

### Option 3: Systemd Service (Linux)
See `docs/TELEGRAM_BOT_SETUP.md` for details

---

## 🐛 Troubleshooting

See the **[Setup Guide](docs/TELEGRAM_BOT_SETUP.md)** troubleshooting section.

Common issues:
- Bot not responding → Check token and bot is running
- Issues not created → Check GitHub token permissions
- No notifications → Check secrets in GitHub repository

---

## 📝 Next Steps

1. ✅ Follow **[Setup Guide](docs/TELEGRAM_BOT_SETUP.md)**
2. ✅ Test with `/help` command
3. ✅ Try `/fix This is a test`
4. ✅ Share **[User Guide](docs/TELEGRAM_BOT_USER_GUIDE.md)** with your wife

---

## 🔒 Security Notes

- ✅ Tokens stored in environment variables
- ✅ `.env` file in `.gitignore`
- ✅ GitHub secrets for CI/CD
- ✅ Optional: Restrict to specific chat IDs

---

**Ready to use!** Start with the [Setup Guide](docs/TELEGRAM_BOT_SETUP.md) →
