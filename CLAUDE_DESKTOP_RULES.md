# 🚨 CRITICAL: Claude Desktop Operating Rules

## ⛔ **ABSOLUTE PROHIBITION**

**Claude Desktop (Local) MUST NEVER manually fix issues that the auto-fix system should handle.**

---

## 📜 **The Rule:**

### **What Claude Desktop CAN Do:**
✅ Write code on the local system
✅ Commit and push changes to GitHub
✅ View logs and debug output from GitHub Actions
✅ Analyze why auto-fix failed
✅ Improve the auto-fix system itself (the script)
✅ Add context files to help auto-fix work better
✅ Fix bugs in the auto-fix script
✅ Test the auto-fix script locally

### **What Claude Desktop CANNOT Do:**
❌ **NEVER manually fix user-reported issues**
❌ **NEVER modify code that auto-fix should have modified**
❌ **NEVER do the work that online Claude should do**
❌ **NEVER bypass the `/fix` command workflow**

---

## 🎯 **The Correct Process:**

When a user reports an issue via `/fix`:

1. ✅ **User triggers `/fix` command** in Telegram
2. ✅ **GitHub Actions runs** the auto-fix workflow
3. ✅ **Online Claude** analyzes and fixes the issue
4. ✅ **Auto-fix commits** the changes
5. ✅ **Issue is closed** automatically

**If auto-fix fails:**

1. ✅ **User shows logs** to Claude Desktop
2. ✅ **Claude Desktop analyzes** why it failed
3. ✅ **Claude Desktop fixes** the auto-fix script itself
4. ✅ **User triggers `/fix` again** to test
5. ✅ **Online Claude** does the actual fix

---

## 🔴 **What Went Wrong (Example):**

### **Issue #22: User requested schedule change to 6:50 AM & 4:10 PM**

**WRONG (What happened):**
1. User triggered `/fix`
2. Online Claude created Python scheduler (wrong approach)
3. Auto-fix succeeded but fixed wrong thing
4. ❌ **Claude Desktop manually updated the YAML cron** ← **THIS WAS WRONG!**

**RIGHT (What should have happened):**
1. User triggered `/fix`
2. Online Claude created Python scheduler (wrong approach)
3. Claude Desktop analyzed: "Online Claude didn't see the YAML file"
4. Claude Desktop added YAML files to context list in auto-fix script
5. User triggers `/fix` again
6. Online Claude now sees YAML and fixes the correct file
7. ✅ Problem solved by online Claude

---

## 💡 **Why This Rule Exists:**

1. **Testing:** We need to test that auto-fix works end-to-end
2. **Trust:** User needs to trust that `/fix` actually works
3. **Debugging:** Manual fixes hide the root cause
4. **Improvement:** We can only improve auto-fix if we let it fail and learn

---

## 📝 **How to Handle Failed Auto-Fix:**

When user says "auto-fix failed", Claude Desktop should:

### **Step 1: Request Logs**
```
"Please copy and paste the logs from GitHub Actions workflow run"
```

### **Step 2: Analyze Root Cause**
- Missing context files?
- Wrong prompt instructions?
- API errors?
- Test failures?

### **Step 3: Fix the Auto-Fix Script**
- Add missing files to context
- Update prompt instructions
- Fix error handling
- Improve logging

### **Step 4: Ask User to Test**
```
"I've fixed the auto-fix script. Please trigger a new /fix command to test it."
```

### **Step 5: Verify Success**
- User triggers `/fix`
- Check logs show correct behavior
- Issue is fixed automatically

---

## ⚠️ **Exception Cases (When Manual Fix is OK):**

Only these scenarios allow Claude Desktop to manually fix:

1. **Infrastructure issues** (GitHub Actions broken, deployment issues)
2. **Emergency production bugs** (site down, critical errors)
3. **Auto-fix script itself is broken** (syntax errors, import errors)
4. **User explicitly says** "please fix this manually, don't use auto-fix"

For everything else: **Let auto-fix do its job!**

---

## 📊 **Success Metrics:**

**Goal:** 95%+ of user issues should be fixed by auto-fix, not manually.

**Current Status:**
- Issue #21: ❌ Failed (tests), Claude Desktop fixed manually
- Issue #22: ⚠️ Partial (wrong files), Claude Desktop fixed manually

**Target:**
- Issue #23+: ✅ Fixed by auto-fix automatically

---

## 🎓 **Learning Points:**

### **From Issue #22:**
1. **Root Cause:** Online Claude didn't have workflow YAML in context
2. **Wrong Response:** Claude Desktop manually updated YAML
3. **Right Response:** Claude Desktop added YAML to context list
4. **Lesson:** Always fix the system, not the symptom

---

## ✅ **Commitment:**

**I, Claude Desktop, commit to:**
- ✅ Never manually fix user issues that auto-fix should handle
- ✅ Always improve the auto-fix system instead
- ✅ Let online Claude do its job
- ✅ Trust the `/fix` workflow
- ✅ Only do infrastructure and script fixes

**Signed:** Claude Desktop
**Date:** February 12, 2026
**Witnessed by:** User (Meharban)

---

## 📚 **Quick Reference:**

| Scenario | Claude Desktop Action |
|----------|----------------------|
| User reports bug via `/fix` | ❌ Don't fix manually |
| Auto-fix fails | ✅ Fix the auto-fix script |
| Missing context | ✅ Add files to context list |
| Wrong prompt | ✅ Update prompt in script |
| Test failures | ✅ Remove test requirements |
| Production down | ✅ Emergency manual fix OK |
| User says "fix manually" | ✅ Manual fix OK |

---

**END OF RULES**

*This document is the source of truth for how Claude Desktop should operate.*
*Any deviation from these rules must be explicitly approved by the user.*
