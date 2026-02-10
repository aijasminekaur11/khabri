# 🚂 Deploy Telegram Bot to Railway (FREE 24/7)

**Run your Telegram bot 24/7 for FREE without keeping your PC on!**

---

## 🎯 **What You'll Get**

- ✅ Bot runs 24/7 automatically
- ✅ Completely FREE (500 hours/month)
- ✅ Auto-restarts if it crashes
- ✅ Easy to update
- ✅ No credit card needed

---

## 📋 **Quick Setup (10 Minutes)**

### **Step 1: Create Railway Account**

1. **Go to**: https://railway.app
2. **Click** "Login" (top-right)
3. **Sign up with GitHub** (easiest option)
4. **Authorize Railway** to access your GitHub

✅ **Done!** You now have a Railway account.

---

### **Step 2: Push Code to GitHub**

Your code needs to be on GitHub first.

**Run these commands in your terminal:**

```bash
cd "D:\Meharban\phase 2 updation\News_Update"
git add Procfile runtime.txt railway.json
git commit -m "Add Railway deployment files"
git push origin main
```

✅ **Done!** Your code is ready for deployment.

---

### **Step 3: Create New Project on Railway**

1. **Go to**: https://railway.app/dashboard
2. **Click** "+ New Project"
3. **Select** "Deploy from GitHub repo"
4. **Choose** your repository: `aijasminekaur11/khabri`
5. **Click** "Deploy Now"

Railway will start deploying automatically!

---

### **Step 4: Add Environment Variables**

Your bot needs the tokens. Add them to Railway:

1. **Click** on your deployed project
2. **Click** "Variables" tab (left sidebar)
3. **Click** "+ New Variable"
4. **Add these 4 variables:**

| Variable Name | Value | Where to get it |
|--------------|-------|-----------------|
| `TELEGRAM_BOT_TOKEN` | Your bot token | From @BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID | From getUpdates API |
| `GH_TOKEN` | Your GitHub token | From GitHub settings |
| `GITHUB_REPO` | `aijasminekaur11/khabri` | Your repo name |

**How to add each variable:**
- Click "+ New Variable"
- Name: `TELEGRAM_BOT_TOKEN`
- Value: Paste your actual token
- Click "Add"
- Repeat for all 4 variables

---

### **Step 5: Deploy!**

1. After adding all variables, Railway will **auto-deploy**
2. **Wait 2-3 minutes** for deployment to complete
3. **Check logs** to see if bot is running:
   - Click "Deployments" tab
   - Click on the latest deployment
   - You should see: "🚀 BOT IS NOW RUNNING"

---

## ✅ **Verify It's Working**

### **1. Check Deployment Logs**

In Railway dashboard:
- Click "Deployments"
- Click latest deployment
- Look for: "✅ Bot initialized successfully"

### **2. Test on Telegram**

Open Telegram and send to your bot:

```
/help
```

You should get a response!

---

## 🔧 **Managing Your Bot**

### **View Logs**

To see what your bot is doing:

1. Go to Railway dashboard
2. Click your project
3. Click "Deployments"
4. Click "View Logs"

### **Restart Bot**

If something goes wrong:

1. Go to Railway dashboard
2. Click your project
3. Click "Settings" → "Restart"

### **Update Bot Code**

When you make changes to your code:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Railway will **automatically redeploy** with your changes!

---

## 💰 **Free Tier Limits**

Railway free tier includes:

- **500 hours/month** (enough for 24/7 operation)
- **100 GB bandwidth**
- **1 GB RAM**
- **1 GB storage**

**Note:** After using 500 hours, you'll need to add a credit card (still free for basic usage) or wait until next month.

---

## 🐛 **Troubleshooting**

### **Bot Not Starting**

**Check:**
1. All 4 environment variables are set correctly
2. No typos in variable names
3. Values don't have extra spaces or quotes
4. Check deployment logs for errors

### **Bot Stopped Working**

**Check:**
1. Railway free hours remaining
2. Deployment logs for errors
3. Restart the deployment

### **Can't Find Deployment Logs**

**Steps:**
1. Railway Dashboard
2. Click your project name
3. Click "Deployments" (left sidebar)
4. Click on latest deployment
5. Scroll down to see logs

---

## 📊 **Monitor Your Bot**

Railway dashboard shows:

- ✅ **CPU Usage** - How much processing power
- ✅ **Memory Usage** - RAM consumption
- ✅ **Network Usage** - Data transfer
- ✅ **Uptime** - How long bot has been running

---

## 🔒 **Security**

Railway keeps your secrets safe:

- ✅ Environment variables are encrypted
- ✅ Not visible in logs
- ✅ Not accessible from outside
- ✅ Separate from your code

---

## 🚀 **Advanced: Custom Domain (Optional)**

You can add a custom domain if needed:

1. Railway Dashboard → Settings
2. Click "Generate Domain"
3. Or add your own domain

**Note:** Your bot doesn't need a domain to work!

---

## 💡 **Tips**

### **Save Money**

The bot uses very little resources. To maximize free tier:

- ✅ Keep bot code efficient
- ✅ Don't run unnecessary processes
- ✅ Monitor usage in Railway dashboard

### **Multiple Bots**

You can run multiple bots on Railway:

- Each bot = separate project
- Each project counts toward 500 hours
- 3-4 bots easily fit in free tier

---

## 📱 **Alternative FREE Options**

If Railway doesn't work for you:

### **1. Render.com**
- FREE tier available
- 750 hours/month
- Easy deployment
- URL: https://render.com

### **2. Fly.io**
- FREE tier: 3 VMs
- Good for bots
- URL: https://fly.io

### **3. Replit (Always On)**
- FREE tier available
- Great for simple bots
- URL: https://replit.com

---

## 🎓 **Quick Reference**

### **Deploy Command**
```bash
git push origin main
```
(Railway auto-deploys on push)

### **View Logs**
Railway Dashboard → Deployments → View Logs

### **Restart**
Railway Dashboard → Settings → Restart

### **Update Variables**
Railway Dashboard → Variables → Edit

---

## 📞 **Need Help?**

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **GitHub Issues**: Create issue in your repo

---

## ✅ **Deployment Checklist**

- [ ] Railway account created
- [ ] Code pushed to GitHub
- [ ] Project created on Railway
- [ ] All 4 environment variables added
- [ ] Deployment successful (check logs)
- [ ] Bot responding to `/help` on Telegram
- [ ] Bot running 24/7

---

**Total Setup Time: ~10 minutes** ⏱️

Your bot will now run 24/7 without your PC being on! 🎉
