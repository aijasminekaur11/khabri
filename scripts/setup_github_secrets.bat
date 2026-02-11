@echo off
REM Setup GitHub Secrets for Auto-Fix Workflow
REM Run this script to add all required secrets to GitHub

echo ============================================================
echo GITHUB SECRETS SETUP
echo ============================================================
echo.
echo This script will add the following secrets to your repository:
echo - TELEGRAM_BOT_TOKEN
echo - TELEGRAM_CHAT_ID
echo - GH_TOKEN
echo - ANTHROPIC_API_KEY
echo - GMAIL_ADDRESS
echo - GMAIL_APP_PASSWORD
echo.
echo Repository: aijasminekaur11/khabri
echo.
echo ============================================================
echo.

REM Load environment variables from .env
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    set "%%a=%%b"
)

echo Adding secrets to GitHub...
echo.

REM Add Telegram secrets
gh secret set TELEGRAM_BOT_TOKEN --body "%TELEGRAM_BOT_TOKEN%" --repo aijasminekaur11/khabri
if %errorlevel% equ 0 (
    echo [OK] TELEGRAM_BOT_TOKEN added
) else (
    echo [FAIL] TELEGRAM_BOT_TOKEN failed
)

gh secret set TELEGRAM_CHAT_ID --body "%TELEGRAM_CHAT_ID%" --repo aijasminekaur11/khabri
if %errorlevel% equ 0 (
    echo [OK] TELEGRAM_CHAT_ID added
) else (
    echo [FAIL] TELEGRAM_CHAT_ID failed
)

REM Add GitHub token
gh secret set GH_TOKEN --body "%GH_TOKEN%" --repo aijasminekaur11/khabri
if %errorlevel% equ 0 (
    echo [OK] GH_TOKEN added
) else (
    echo [FAIL] GH_TOKEN failed
)

REM Add Claude API key
gh secret set ANTHROPIC_API_KEY --body "%ANTHROPIC_API_KEY%" --repo aijasminekaur11/khabri
if %errorlevel% equ 0 (
    echo [OK] ANTHROPIC_API_KEY added
) else (
    echo [FAIL] ANTHROPIC_API_KEY failed
)

REM Add Gmail secrets
gh secret set GMAIL_ADDRESS --body "%GMAIL_ADDRESS%" --repo aijasminekaur11/khabri
if %errorlevel% equ 0 (
    echo [OK] GMAIL_ADDRESS added
) else (
    echo [FAIL] GMAIL_ADDRESS failed
)

gh secret set GMAIL_APP_PASSWORD --body "%GMAIL_APP_PASSWORD%" --repo aijasminekaur11/khabri
if %errorlevel% equ 0 (
    echo [OK] GMAIL_APP_PASSWORD added
) else (
    echo [FAIL] GMAIL_APP_PASSWORD failed
)

echo.
echo ============================================================
echo DONE!
echo ============================================================
echo.
echo All secrets have been added to GitHub.
echo Your automated workflows should now work correctly.
echo.
echo To verify, visit:
echo https://github.com/aijasminekaur11/khabri/settings/secrets/actions
echo.
pause
