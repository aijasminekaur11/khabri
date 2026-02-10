# 🔐 Add Claude API Key to GitHub Secrets

**CRITICAL STEP for Full Automation!**

Without this, Claude can only analyze issues. With this, Claude WRITES CODE automatically!

---

## 📋 **Quick Steps (2 minutes)**

### Step 1: Go to GitHub Secrets Page

**URL**: https://github.com/aijasminekaur11/khabri/settings/secrets/actions

Or navigate manually:
1. Go to your repository: https://github.com/aijasminekaur11/khabri
2. Click "Settings" tab (top right)
3. Click "Secrets and variables" → "Actions" (left sidebar)

---

### Step 2: Add New Secret

1. **Click**: "New repository secret" (green button, top right)

2. **Fill in the form:**
   - **Name**: `ANTHROPIC_API_KEY`
   - **Secret**: Your Claude API key from `.env` file (starts with `sk-ant-`)

3. **Click**: "Add secret"

**Where to find your API key:**
- Open the `.env` file in your project
- Copy the value after `ANTHROPIC_API_KEY=`
- It starts with `sk-ant-api03-`

---

## ✅ **Verify It's Added**

After adding, you should see:

```
ANTHROPIC_API_KEY    Updated XXX ago
GH_TOKEN             Updated XXX ago
TELEGRAM_BOT_TOKEN   Updated XXX ago
TELEGRAM_CHAT_ID     Updated XXX ago
```

If you see `ANTHROPIC_API_KEY` in the list, **you're done!** ✅

---

## 🧪 **Test Full Automation**

Send on Telegram:
```
/fix Add a simple hello world test function
```

You should get:
1. ✅ **Issue created**
2. 🤖 **Claude analysis complete**
3. ⏳ **GitHub Actions running** (check https://github.com/aijasminekaur11/khabri/actions)
4. 🔧 **Pull Request created** with actual code changes!
5. 📱 **Telegram notification** when PR is ready

---

## 🎯 **What Changes After Adding This**

### Before (What You Have Now):
```
/fix command
    ↓
Issue created ✅
    ↓
Claude analyzes issue ✅
    ↓
Analysis posted as comment ✅
    ↓
❌ Auto-Fix Failed (manual review required)
```

### After (Full Automation):
```
/fix command
    ↓
Issue created ✅
    ↓
Claude analyzes issue ✅
    ↓
Claude WRITES CODE ✅
    ↓
Pull Request created ✅
    ↓
Tests run automatically ✅
    ↓
Telegram notification: "PR ready!" ✅
```

---

## 💰 **Cost**

- **Analysis only**: $0.005 per fix
- **Full auto-fix**: $0.02 per fix

Still very cheap with Claude Max plan!

---

## 🐛 **Troubleshooting**

### "Secret not found" error in GitHub Actions

- Make sure the name is exactly: `ANTHROPIC_API_KEY` (case-sensitive)
- No spaces before or after the name
- The secret value should start with `sk-ant-`

### Still seeing "Auto-Fix Failed"

1. Wait 1-2 minutes after adding the secret
2. Try a new `/fix` command (not an old issue)
3. Check GitHub Actions logs for errors

---

**Add this secret NOW to enable full automation!** 🚀
