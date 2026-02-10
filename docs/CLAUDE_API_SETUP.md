# 🤖 Claude API Integration Setup

Complete auto-fix powered by Claude AI!

---

## 📋 **Step 1: Get Your Claude API Key**

1. **Go to**: https://console.anthropic.com/
2. **Sign in** with your Anthropic account
3. **Click** "API Keys" in the left sidebar
4. **Click** "Create Key"
5. **Name**: "Telegram Bot Auto-Fix"
6. **Copy the key** (starts with `sk-ant-`)

⚠️ **Save it now** - you won't see it again!

---

## 📋 **Step 2: Add API Key to Local Environment**

Edit your `.env` file:

```bash
# Add this line (replace with your actual key):
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

---

## 📋 **Step 3: Add API Key to Railway**

1. **Go to** Railway dashboard
2. **Click** on your "worker" service
3. **Click** "Variables" tab
4. **Add new variable**:
   - **Name**: `ANTHROPIC_API_KEY`
   - **Value**: Your Claude API key
5. **Save** - Railway will auto-redeploy

---

## 🧪 **Step 4: Test Locally**

```bash
python scripts/run_telegram_bot.py
```

Then send on Telegram:
```
/fix Add pagination to the news list
```

You should get:
- ✅ Issue created
- 🤖 Claude analysis posted
- 📊 Token usage shown

---

## ✅ **What Happens Now**

### **Before (Manual):**
```
/fix command → Issue created → Manual review required
```

### **After (Automatic with Claude):**
```
/fix command
    ↓
Issue created ✅
    ↓
Claude analyzes issue 🤖
    ↓
Analysis posted to GitHub ✅
    ↓
User gets AI-powered insights ✅
    ↓
(Future: Auto-create PR with fix) 🚀
```

---

## 🎯 **Current Features**

✅ **Automatic Issue Analysis**
- Claude reads the issue description
- Identifies root cause
- Suggests fix approach
- Posts detailed analysis as GitHub comment

✅ **Smart Notifications**
- Telegram shows analysis preview
- Full analysis on GitHub
- Token usage tracking

✅ **Cost Tracking**
- Each analysis: ~1,000-2,000 tokens
- Cost: ~$0.003-$0.006 per analysis
- With Claude Max plan: Extremely affordable!

---

## 💰 **Cost Breakdown**

### **Claude API Pricing:**
- **Claude Sonnet 4**: $3 per million input tokens
- **Average fix analysis**: 1,500 tokens = $0.0045

### **Monthly Estimate:**
- 10 fixes/day = 300 fixes/month
- 300 × $0.0045 = **$1.35/month**

**With your Claude Max plan**, this is essentially free! 🎉

---

## 🔧 **Advanced: Adding Auto-PR Creation**

Want Claude to create actual pull requests with code fixes?

This requires:
1. ✅ Claude API key (you have this!)
2. 🆕 Access to your codebase files
3. 🆕 Ability to create branches and PRs

Let me know if you want to add this feature!

---

## 🐛 **Troubleshooting**

### **"Claude API not configured"**
- Check `ANTHROPIC_API_KEY` in `.env`
- Verify it starts with `sk-ant-`
- No spaces or quotes around the key

### **"Analysis failed"**
- Check API key is valid
- Verify you have API credits
- Check Railway logs for errors

### **Railway not updating**
- Make sure you added `ANTHROPIC_API_KEY` to Railway Variables
- Wait 1-2 minutes for redeploy
- Check deployment logs

---

## 📊 **Monitoring Usage**

Check your API usage at:
https://console.anthropic.com/settings/usage

You'll see:
- Tokens used per day
- Cost breakdown
- API calls made

---

## 🎉 **Success Checklist**

- [ ] Got Claude API key from console.anthropic.com
- [ ] Added `ANTHROPIC_API_KEY` to `.env` file
- [ ] Added `ANTHROPIC_API_KEY` to Railway Variables
- [ ] Tested `/fix` command locally
- [ ] Saw Claude analysis in GitHub comment
- [ ] Deployed to Railway
- [ ] Tested from Telegram

---

**Once setup, every `/fix` command will include AI-powered analysis!** 🤖✨
