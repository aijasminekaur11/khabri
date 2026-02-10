# ✅ Telegram Bot Setup Checklist

**Follow these steps to get your wife's Telegram bot working!**

---

## 📋 Step-by-Step Checklist

### ☐ Step 1: Create Telegram Bot (5 minutes)

1. ☐ Open Telegram on your phone
2. ☐ Search for `@BotFather`
3. ☐ Send `/newbot` command
4. ☐ Choose name: "Khabri Assistant" (or any name)
5. ☐ Choose username: "khabri_fix_bot" (must end in 'bot')
6. ☐ **Copy the bot token** (looks like: `1234567890:ABCdef...`)
7. ☐ Save token somewhere safe

**Result:** You have a bot token ✅

---

### ☐ Step 2: Get Your Chat ID (2 minutes)

1. ☐ Open your new bot in Telegram
2. ☐ Send any message: "Hello"
3. ☐ Open this URL in browser (replace YOUR_BOT_TOKEN):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
4. ☐ Find your chat ID (number like `123456789`)
5. ☐ Save chat ID

**Result:** You have a chat ID ✅

---

### ☐ Step 3: Create GitHub Token (3 minutes)

1. ☐ Go to: https://github.com/settings/tokens
2. ☐ Click "Generate new token (classic)"
3. ☐ Name: "Telegram Bot Access"
4. ☐ Select permissions:
   - ☐ `repo` (full control)
   - ☐ `workflow` (update workflows)
5. ☐ Click "Generate token"
6. ☐ **Copy and save the token** (you won't see it again!)

**Result:** You have a GitHub token ✅

---

### ☐ Step 4: Add Secrets to GitHub (3 minutes)

1. ☐ Go to: https://github.com/aijasminekaur11/khabri/settings/secrets/actions
2. ☐ Click "New repository secret"
3. ☐ Add secret #1:
   - Name: `TELEGRAM_BOT_TOKEN`
   - Value: (paste your bot token from Step 1)
4. ☐ Add secret #2:
   - Name: `TELEGRAM_CHAT_ID`
   - Value: (paste your chat ID from Step 2)
5. ☐ Add secret #3:
   - Name: `GH_TOKEN`
   - Value: (paste your GitHub token from Step 3)

**Result:** All secrets added to GitHub ✅

---

### ☐ Step 5: Create .env File (2 minutes)

1. ☐ Open your project folder
2. ☐ Create a new file named `.env`
3. ☐ Add these lines (replace with your actual values):
   ```
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789
   GH_TOKEN=ghp_your_github_token_here
   GITHUB_REPO=aijasminekaur11/khabri
   ```
4. ☐ Save the file

**Result:** .env file created ✅

---

### ☐ Step 6: Install Dependencies (1 minute)

Open terminal in your project folder and run:

```bash
pip install -r requirements-telegram-bot.txt
```

**Result:** Dependencies installed ✅

---

### ☐ Step 7: Test the Bot (2 minutes)

1. ☐ Run the bot:
   ```bash
   python scripts/run_telegram_bot.py
   ```

2. ☐ You should see:
   ```
   ✅ Bot initialized successfully
   🚀 BOT IS NOW RUNNING
   ```

3. ☐ Open Telegram on your phone
4. ☐ Find your bot
5. ☐ Send: `/help`
6. ☐ Bot should respond with help message

**Result:** Bot is working! ✅

---

### ☐ Step 8: Test Fix Command (2 minutes)

1. ☐ Send in Telegram:
   ```
   /fix This is a test fix request
   ```

2. ☐ Bot should respond:
   ```
   🔄 Creating fix request...
   ✅ Fix request created successfully!
   📋 Issue: #XXX
   ```

3. ☐ Go to GitHub: https://github.com/aijasminekaur11/khabri/issues
4. ☐ Verify new issue was created with "auto-fix" label

**Result:** Fix command working! ✅

---

### ☐ Step 9: Share with Your Wife (1 minute)

1. ☐ Send her the bot username
2. ☐ Send her this file: `docs/TELEGRAM_BOT_USER_GUIDE.md`
3. ☐ Tell her to start with `/help`

**Result:** Your wife can now use the bot! ✅

---

## 🎉 Complete Setup Summary

Once all steps are done:

✅ Telegram bot created
✅ Bot token obtained
✅ Chat ID obtained
✅ GitHub token created
✅ All secrets added to GitHub
✅ .env file created
✅ Dependencies installed
✅ Bot tested and working
✅ Wife can send fix requests

---

## 🚀 Next Steps

### For You:
- Keep bot running: `python scripts/run_telegram_bot.py`
- Or deploy to cloud server (see `docs/TELEGRAM_BOT_SETUP.md`)

### For Your Wife:
- Send `/fix <problem>` to request fixes
- Send `/status` to check progress
- Send `/help` for commands

---

## 🐛 Troubleshooting

**Bot not responding?**
- ☐ Check bot is running
- ☐ Verify token in .env is correct
- ☐ Check internet connection

**Issues not created?**
- ☐ Verify GH_TOKEN has correct permissions
- ☐ Check GitHub secrets are set
- ☐ Verify repository name is correct

**Can't find bot?**
- ☐ Search for bot username in Telegram
- ☐ Make sure you sent a message first

---

## 📞 Need Help?

Full guides available:
- **Technical Setup**: `docs/TELEGRAM_BOT_SETUP.md`
- **User Guide**: `docs/TELEGRAM_BOT_USER_GUIDE.md`
- **Main README**: `TELEGRAM_BOT_README.md`

---

**Total Setup Time: ~20 minutes** ⏱️

Good luck! 🎉
