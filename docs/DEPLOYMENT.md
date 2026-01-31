# Khabri Deployment Guide

## Quick Start (5 Minutes)

### Step 1: Set Up Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow prompts to create your bot
4. Copy the **bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`)
5. Add bot to your group/channel
6. Get chat ID:
   - Send a message in your group
   - Open: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Find `"chat":{"id": -123456789}` (negative number for groups)

### Step 2: Set Up Email (Optional)

For Gmail:
1. Enable 2-Factor Authentication on Google account
2. Go to: https://myaccount.google.com/apppasswords
3. Generate an App Password for "Mail"

### Step 3: Configure Environment

```bash
# Navigate to project
cd D:\Jasmine\00001_Content_app\News_Update

# Copy example env file
copy .env.example .env

# Edit .env with your credentials
notepad .env
```

Fill in your `.env`:
```
TELEGRAM_BOT_TOKEN=your_actual_token
TELEGRAM_CHAT_ID=your_actual_chat_id
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_RECIPIENT=recipient@example.com
```

### Step 4: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Run the System

```bash
python main.py
```

You should see:
```
╔═══════════════════════════════════════════════════════════╗
║   🗞️  KHABRI - News Intelligence System  🗞️              ║
╚═══════════════════════════════════════════════════════════╝

Initializing Khabri News Intelligence System...
Telegram notifier initialized
Email notifier initialized
Khabri initialized successfully!
Starting main loop (checking every 60s)...
```

---

## Deployment Options

### Option A: Run on Your PC (Simple)

**Pros:** Easy, no cost
**Cons:** Stops when PC is off

```bash
# Just run it
python main.py

# Or run in background (Windows)
start /B python main.py > logs\output.log 2>&1
```

### Option B: Windows Task Scheduler (Recommended for PC)

1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task → Name: "Khabri News System"
3. Trigger: "When the computer starts"
4. Action: Start a program
   - Program: `D:\Jasmine\00001_Content_app\News_Update\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `D:\Jasmine\00001_Content_app\News_Update`
5. Check: "Run with highest privileges"
6. Check: "Run whether user is logged on or not"

### Option C: Cloud Deployment (24/7 Uptime)

#### Free Options:

1. **PythonAnywhere** (Free tier available)
   - Sign up at pythonanywhere.com
   - Upload code
   - Set up scheduled task

2. **Heroku** (Free tier)
   ```bash
   # Create Procfile
   echo "worker: python main.py" > Procfile

   # Deploy
   heroku create khabri-news
   heroku config:set TELEGRAM_BOT_TOKEN=xxx
   heroku config:set TELEGRAM_CHAT_ID=xxx
   git push heroku main
   ```

3. **Railway.app** (Free tier)
   - Connect GitHub repo
   - Add environment variables
   - Deploy

#### Paid Options (More Reliable):

1. **AWS EC2** (~$5/month)
2. **DigitalOcean Droplet** (~$4/month)
3. **Google Cloud Run** (Pay per use)

---

## Schedule Configuration

### Current Schedule (Default):

| Time | Action |
|------|--------|
| 7:00 AM | Morning Digest (Telegram + Email) |
| 4:00 PM | Evening Digest (Telegram only) |
| Every 15 min | Real-time alerts for breaking news |

### Modify Schedule:

Edit `config/schedules.yaml`:

```yaml
digests:
  morning:
    enabled: true
    time: "07:00"  # Change this time
```

---

## Testing Your Setup

### Test Telegram:

```bash
python -c "
from src.notifiers import TelegramNotifier
import os
from dotenv import load_dotenv
load_dotenv()

telegram = TelegramNotifier(
    bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
    default_chat_id=os.getenv('TELEGRAM_CHAT_ID')
)
import asyncio
asyncio.run(telegram.send_message('Test from Khabri!'))
print('Telegram test sent!')
"
```

### Test Email:

```bash
python -c "
from src.notifiers import EmailNotifier
import os
from dotenv import load_dotenv
load_dotenv()

email = EmailNotifier(
    smtp_host=os.getenv('SMTP_HOST'),
    smtp_port=int(os.getenv('SMTP_PORT', 587)),
    username=os.getenv('SMTP_USERNAME'),
    password=os.getenv('SMTP_PASSWORD'),
    sender_email=os.getenv('SMTP_USERNAME'),
    default_recipients=[os.getenv('EMAIL_RECIPIENT')]
)
import asyncio
asyncio.run(email.send_email('Khabri Test', 'This is a test email from Khabri!'))
print('Email test sent!')
"
```

---

## Troubleshooting

### "Telegram not configured"
- Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
- Make sure bot is added to the group/channel

### "Email not configured"
- Verify SMTP credentials
- For Gmail, use App Password (not regular password)

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Permission denied" on Windows
- Run as Administrator
- Check antivirus isn't blocking

---

## Monitoring

### View Logs:
```bash
# Real-time logs
tail -f logs/khabri.log

# Windows equivalent
Get-Content logs\khabri.log -Wait
```

### Check Status:
The system logs its activity every minute. Check `logs/khabri.log` for:
- Scraping activity
- Digest sends
- Errors

---

## Summary Checklist

- [ ] Created Telegram bot and got token
- [ ] Got Telegram chat ID
- [ ] (Optional) Set up Gmail App Password
- [ ] Created `.env` file with credentials
- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] Ran `python main.py` successfully
- [ ] Received test notification

**Your system will automatically:**
- Send Morning Digest at 7:00 AM
- Send Evening Digest at 4:00 PM
- Alert on breaking news/celebrity mentions

---

## Support

For issues, check:
1. `logs/khabri.log` for errors
2. GitHub Issues: https://github.com/aijasminekaur11/khabri/issues
