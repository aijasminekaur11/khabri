# Jasmine's Quick Guide to Khabri
# ================================

## How It Works (Super Simple!)

1. **You type** what you want in Claude.ai
2. **Claude tells** you exactly what to copy/paste where
3. **You save** and push to GitHub
4. **Done!** Changes go live automatically

---

## Example Conversations

### ➕ ADDING Things

**You say:** "Add Hindu Business Line as a news source"

**Claude will say:**
> Open `config/sources.yaml` and add this under `news_sources:`:
> ```yaml
>   - name: "Hindu Business Line"
>     url: "https://www.thehindubusinessline.com/real-estate/"
>     enabled: true
>     frequency_minutes: 60
> ```
> Then run: `git add . && git commit -m "Added Hindu Business Line" && git push`

---

**You say:** "Track keyword 'green building'"

**Claude will say:**
> Open `config/keywords.yaml` and add `"green building"` under the appropriate category.
> Then push to GitHub.

---

### ➖ REMOVING Things

**You say:** "Stop tracking 99acres blog"

**Claude will say:**
> Open `config/sources.yaml`, find `99acres` section, and change:
> ```yaml
> enabled: true
> ```
> to:
> ```yaml
> enabled: false
> ```
> Then push to GitHub.

---

**You say:** "Remove NoBroker from competitors"

**Claude will say:**
> Open `config/sources.yaml`, find the NoBroker section and delete the entire block:
> ```yaml
>   - name: "NoBroker Blog"
>     url: "https://www.nobroker.in/blog/"
>     ...
> ```
> Then push to GitHub.

---

### 🔄 CHANGING Things

**You say:** "Change morning digest to 8 AM"

**Claude will say:**
> Open `.github/workflows/scheduled-digest.yml` and find:
> ```yaml
> - cron: '30 1 * * *'  # 7:00 AM IST
> ```
> Change to:
> ```yaml
> - cron: '30 2 * * *'  # 8:00 AM IST
> ```
> Then push to GitHub.

---

### 📅 ADDING Events

**You say:** "Add RBI meeting alert on Feb 7 from 10 AM to 1 PM"

**Claude will say:**
> Open `config/schedules.yaml` and add under `events:`:
> ```yaml
>   - name: "RBI Policy Review"
>     date: "2026-02-07"
>     start_time: "10:00"
>     end_time: "13:00"
>     enabled: true
>     keywords:
>       - "RBI"
>       - "repo rate"
>       - "interest rate"
> ```
> Then I'll help you create the GitHub Action for it.

---

## Quick Reference

| You Want To | File to Edit |
|-------------|--------------|
| Add/remove news source | `config/sources.yaml` |
| Add/remove keyword | `config/keywords.yaml` |
| Add/remove celebrity | `config/celebrities.yaml` |
| Change schedule time | `.github/workflows/scheduled-digest.yml` |
| Add special event | `config/schedules.yaml` + create workflow |

---

## After Every Change

Run these 3 commands:
```
git add .
git commit -m "Your change description"
git push
```

Or just tell Claude "I made the change" and Claude will give you the exact commands!

---

## Key Points

✅ **Adding** = Just add new lines to config files
✅ **Removing** = Delete lines OR set `enabled: false`
✅ **Changing** = Edit existing values
✅ **Always push to GitHub** after changes

---

## Your Files Location

```
D:\Jasmine\00001_Content_app\News_Update\
├── config/
│   ├── sources.yaml      ← News sources
│   ├── keywords.yaml     ← Keywords
│   ├── schedules.yaml    ← Schedules & Events
│   └── celebrities.yaml  ← Celebrity tracking
└── .github/workflows/
    ├── scheduled-digest.yml  ← Daily digest timing
    └── budget-event.yml      ← Budget alerts
```
