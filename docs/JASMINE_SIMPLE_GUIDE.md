# Jasmine's Super Simple Guide
# ============================
# No coding needed! Just copy-paste on GitHub website!

## How It Works

1. **Ask Claude** what you want
2. **Claude gives you a GitHub link** to the file
3. **Click the link** → Click ✏️ Edit button
4. **Make the change** (copy-paste what Claude gives)
5. **Click "Commit changes"** button
6. **Done!** ✅

---

## File Links (Bookmark These!)

### 📰 News Sources
**https://github.com/aijasminekaur11/khabri/edit/main/config/sources.yaml**

Use for: Add/remove news websites, RSS feeds, competitor blogs

---

### 🔑 Keywords
**https://github.com/aijasminekaur11/khabri/edit/main/config/keywords.yaml**

Use for: Add/remove keywords to track

---

### ⏰ Schedules & Events
**https://github.com/aijasminekaur11/khabri/edit/main/config/schedules.yaml**

Use for: Change digest times, add special events

---

### 👤 Celebrities
**https://github.com/aijasminekaur11/khabri/edit/main/config/celebrities.yaml**

Use for: Add/remove celebrity names to track

---

### 📅 Daily Digest Timing
**https://github.com/aijasminekaur11/khabri/edit/main/.github/workflows/scheduled-digest.yml**

Use for: Change 7 AM / 4 PM timing

---

### 🏛️ Budget Event Alerts
**https://github.com/aijasminekaur11/khabri/edit/main/.github/workflows/budget-event.yml**

Use for: Modify Budget day alerts

---

## Example: How to Add a News Source

**Step 1:** Tell Claude: "Add Times of India Real Estate"

**Step 2:** Claude says:
> Click this link: https://github.com/aijasminekaur11/khabri/edit/main/config/sources.yaml
>
> Find `news_sources:` section and add this at the end:
> ```yaml
>   - name: "Times of India Realty"
>     url: "https://timesofindia.indiatimes.com/business/real-estate"
>     enabled: true
>     frequency_minutes: 30
> ```

**Step 3:** Click the link, paste the text, click "Commit changes"

**Done!** ✅

---

## Example: How to Remove Something

**Step 1:** Tell Claude: "Stop tracking NoBroker"

**Step 2:** Claude says:
> Click this link: https://github.com/aijasminekaur11/khabri/edit/main/config/sources.yaml
>
> Find this line:
> ```yaml
>   - name: "NoBroker Blog"
>     enabled: true
> ```
> Change `true` to `false`:
> ```yaml
>   - name: "NoBroker Blog"
>     enabled: false
> ```

**Step 3:** Make the change, click "Commit changes"

**Done!** ✅

---

## Quick Summary

| You Want | Tell Claude | Claude Gives |
|----------|-------------|--------------|
| Add news source | "Add [website name]" | Link + text to paste |
| Remove source | "Stop tracking [name]" | Link + what to change |
| Add keyword | "Track keyword [word]" | Link + text to paste |
| Add event | "Add [event] on [date]" | Link + text to paste |
| Change time | "Morning digest at 8 AM" | Link + what to change |

---

## That's It!

**No terminal. No code. Just:**
1. Ask Claude
2. Click link
3. Paste
4. Commit

🎉
