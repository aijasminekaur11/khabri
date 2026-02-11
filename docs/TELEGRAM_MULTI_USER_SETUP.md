# Telegram Multi-User Setup Guide

This guide explains how to add multiple Telegram users to receive notifications and use bot commands.

## 🎯 What Changed

Your Telegram bot now supports:
- ✅ **Multiple notification recipients** - Send news digests/alerts to multiple users
- ✅ **Command authorization** - Restrict `/fix`, `/status` commands to authorized users only
- ✅ **Backward compatibility** - Existing single-user setup still works

---

## 📋 Step-by-Step Guide

### **Step 1: Get Your New Chat ID**

To add a new user, you need their Telegram Chat ID.

#### Method A: Using Bot API (Recommended)
1. The new user should open your bot in Telegram
2. Send any message to the bot (e.g., `/start` or `hello`)
3. Open this URL in your browser (replace with your bot token):
   ```
   https://api.telegram.org/bot8380610667:AAFvdgLRdgFLShb4J-lhO6cQ_ToAuJyukv8/getUpdates
   ```
4. Look for the message in the JSON response
5. Find the Chat ID: `"chat":{"id":XXXXXXX}`
6. Copy this number (e.g., `5118231822`)

#### Method B: Using @userinfobot
1. The new user opens [@userinfobot](https://t.me/userinfobot) in Telegram
2. Send any message
3. Bot will reply with their Chat ID

---

### **Step 2: Update Your `.env` File**

Edit `D:\Meharban\phase 2 updation\News_Update\.env`

#### **For Multiple Notification Recipients:**

Change this line:
```env
TELEGRAM_CHAT_ID=5118231822
```

To this (add new IDs separated by commas):
```env
TELEGRAM_CHAT_ID=5118231822,987654321,123456789
```

#### **For Bot Command Authorization:**

Add or update this line:
```env
TELEGRAM_AUTHORIZED_IDS=5118231822,987654321
```

**Note:** Only users in `TELEGRAM_AUTHORIZED_IDS` can use `/fix`, `/status`, `/help` commands.

---

### **Step 3: Restart the Bot**

If the bot is running, stop it (Ctrl+C) and restart:

```bash
python scripts/run_telegram_bot.py
```

You should see:
```
Bot authorization enabled for 2 chat(s)
```

---

## 🔧 Configuration Examples

### Example 1: Two Users, Both Can Use Commands
```env
TELEGRAM_CHAT_ID=5118231822,987654321
TELEGRAM_AUTHORIZED_IDS=5118231822,987654321
```

### Example 2: Three Users Get Notifications, Only Two Can Use Commands
```env
TELEGRAM_CHAT_ID=5118231822,987654321,123456789
TELEGRAM_AUTHORIZED_IDS=5118231822,987654321
```

### Example 3: One User, No Authorization Check (Anyone Can Use Bot)
```env
TELEGRAM_CHAT_ID=5118231822
# Leave TELEGRAM_AUTHORIZED_IDS empty or comment it out
```

---

## 🧪 Testing the Setup

### Test 1: Check Notifications (TelegramNotifier)

Run a test script or trigger a notification. All users in `TELEGRAM_CHAT_ID` should receive the message.

### Test 2: Check Bot Commands (TelegramBotHandler)

From each authorized user's account, send:
```
/help
```

**Expected results:**
- ✅ Authorized users: Receive help message
- ❌ Unauthorized users: Receive "Access Denied" message with their Chat ID

### Test 3: Test `/fix` Command

From an authorized account:
```
/fix Test issue - multiple user support
```

Should create a GitHub issue and respond with confirmation.

---

## 📊 What Each Environment Variable Does

| Variable | Purpose | Format | Required |
|----------|---------|--------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot authentication | Single token | ✅ Yes |
| `TELEGRAM_CHAT_ID` | Who receives notifications | Comma-separated IDs | ✅ Yes |
| `TELEGRAM_AUTHORIZED_IDS` | Who can use bot commands | Comma-separated IDs | ⚠️ Optional |

---

## 🔍 Troubleshooting

### Issue: "Access Denied" message
**Cause:** User's Chat ID is not in `TELEGRAM_AUTHORIZED_IDS`

**Solution:** Add their Chat ID to `.env`:
```env
TELEGRAM_AUTHORIZED_IDS=5118231822,NEW_CHAT_ID
```

### Issue: User not receiving notifications
**Cause:** User's Chat ID is not in `TELEGRAM_CHAT_ID`

**Solution:** Add their Chat ID:
```env
TELEGRAM_CHAT_ID=5118231822,NEW_CHAT_ID
```

### Issue: Bot accepts commands from anyone
**Cause:** `TELEGRAM_AUTHORIZED_IDS` is not set

**Solution:** Set authorized IDs in `.env`:
```env
TELEGRAM_AUTHORIZED_IDS=5118231822
```

### Issue: "Unauthorized access attempt" in logs
**Expected behavior:** This means the security is working correctly. Only authorized users can use the bot.

---

## 🔒 Security Best Practices

1. **Always set `TELEGRAM_AUTHORIZED_IDS`** - Don't let anyone use your bot
2. **Keep your `.env` file private** - Never commit it to GitHub
3. **Use GitHub Secrets** for production deployments
4. **Regularly review authorized users** - Remove users who no longer need access
5. **Monitor logs** for unauthorized access attempts

---

## 📝 Code Changes Summary

### Files Modified:
1. **`src/notifiers/telegram_notifier.py`**
   - Now supports multiple chat IDs in `__init__`
   - `_send_message()` sends to all configured IDs

2. **`src/notifiers/telegram_bot_handler.py`**
   - Added authorization check in `__init__`
   - `process_message()` validates user access

3. **`.env`**
   - Added comments for multi-user format
   - Added `TELEGRAM_AUTHORIZED_IDS` variable

4. **`.env.example`**
   - Updated with multi-user examples

---

## 🚀 Quick Reference Commands

### Get Updates (Find Chat ID)
```bash
curl https://api.telegram.org/bot8380610667:AAFvdgLRdgFLShb4J-lhO6cQ_ToAuJyukv8/getUpdates
```

### Test Telegram Connection
```bash
python scripts/check_telegram_setup.py
```

### Run Bot
```bash
python scripts/run_telegram_bot.py
```

---

## 📞 Need Help?

If you encounter issues:
1. Check the logs: `logs/telegram_bot.log`
2. Verify environment variables are set correctly
3. Ensure Chat IDs are correct (no quotes, just numbers)
4. Restart the bot after `.env` changes

---

**Last Updated:** 2026-02-11
**Version:** 1.0 - Multi-User Support
