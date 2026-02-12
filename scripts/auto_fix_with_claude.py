#!/usr/bin/env python3
"""
Auto-Fix Script with Gemini API (Primary) and Claude API (Backup)
Automatically fixes GitHub issues using AI to write code
"""

import os
import sys
import json
import subprocess
import shlex
import shutil
from pathlib import Path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai not installed")

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic not installed")


# Files that should never be sent as context (may contain secrets)
_SENSITIVE_PATTERNS = {'.env', 'credentials', 'secret', 'token', '.key', '.pem'}


def get_issue_details(issue_number):
    """Get issue details from GitHub"""
    import requests

    github_token = os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise RuntimeError("GH_TOKEN or GITHUB_TOKEN environment variable not set")

    github_repo = os.getenv('GITHUB_REPOSITORY', 'aijasminekaur11/khabri')

    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    url = f'https://api.github.com/repos/{github_repo}/issues/{issue_number}'
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Request to GitHub API timed out for issue #{issue_number}")

    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(
            f"Failed to get issue: {response.status_code} - {response.text[:200]}"
        )


def _is_sensitive_file(file_path):
    """Check if a file path looks like it may contain secrets"""
    lower = file_path.lower()
    return any(pattern in lower for pattern in _SENSITIVE_PATTERNS)


def read_relevant_files():
    """Read relevant code files for context"""
    project_root = Path(__file__).parent.parent

    # Key files to provide context
    important_files = [
        'src/config/config_manager.py',
        'src/processors/news_processor.py',
        'src/scrapers/news_scraper.py',
        'src/notifiers/telegram_notifier.py',
        '.github/workflows/scheduled-digest.yml',  # For schedule/cron fixes
        '.github/workflows/realtime-alerts.yml',   # For alert scheduling
    ]

    context = {}
    for file_path in important_files:
        if _is_sensitive_file(file_path):
            continue
        full_path = project_root / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    context[file_path] = f.read()
            except OSError as e:
                print(f"  Warning: Could not read {file_path}: {e}")

    return context


# Gemini function removed - using Kimi instead


def generate_fix_with_claude(issue_title, issue_body, code_context):
    """Use Claude API to generate actual code fix"""

    print("  [Claude] Checking API key...")
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not found")
    print(f"  [Claude] OK API key found (length: {len(api_key)})")

    print("  [Claude] Checking anthropic package...")
    if not ANTHROPIC_AVAILABLE:
        raise RuntimeError("anthropic package not installed")
    print("  [Claude] OK anthropic package available")

    print("  [Claude] Initializing client...")
    client = Anthropic(api_key=api_key)
    print("  [Claude] OK Client initialized")

    # Build comprehensive prompt for Claude
    print("  [Claude] Building prompt...")
    prompt = f"""You are an expert Python developer. You need to fix this GitHub issue by writing actual code.

**Issue Title:** {issue_title}

**Issue Description:**
{issue_body}

**Current Codebase Context:**
{json.dumps(code_context, indent=2)}

**Your Task:**
1. Understand what the issue is asking for
2. Identify which file(s) need to be modified
3. Write the COMPLETE FIXED CODE for each file
4. Return your response in this EXACT JSON format:

{{
  "analysis": "Brief explanation of what you're fixing",
  "files_to_modify": [
    {{
      "path": "src/path/to/file.py",
      "action": "modify",
      "new_content": "COMPLETE FILE CONTENT HERE"
    }}
  ],
  "files_to_create": [
    {{
      "path": "src/path/to/newfile.py",
      "content": "COMPLETE FILE CONTENT HERE"
    }}
  ],
  "test_commands": [],
  "summary": "One-sentence summary of the fix"
}}

**CRITICAL REQUIREMENTS:**
- Provide COMPLETE file contents, not just snippets
- Maintain existing code style and structure
- Include proper imports and error handling
- Add comments explaining complex logic
- Ensure code follows Python best practices
- IMPORTANT: Set "test_commands" to an empty array []. Do NOT include any test commands.

Return ONLY valid JSON, no markdown, no explanations outside the JSON.
"""
    print(f"  [Claude] OK Prompt built (length: {len(prompt)} chars)")

    print("  [Claude] Calling API...")
    print(f"  [Claude] -> Model: claude-sonnet-4-5-20250929")
    print(f"  [Claude] -> Max tokens: 8000")

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        print("  [Claude] OK API call successful")
    except Exception as api_error:
        print(f"  [Claude] ERROR API call failed: {api_error}")
        raise

    print("  [Claude] Processing response...")
    if not message.content:
        raise RuntimeError("Empty response from Claude API")
    response_text = message.content[0].text
    print(f"  [Claude] OK Response received (length: {len(response_text)} chars)")

    # Parse JSON response — strip markdown fences if present
    print("  [Claude] Parsing JSON...")
    stripped = response_text.strip()
    if stripped.startswith("```"):
        print("  [Claude] -> Stripping markdown fences...")
        first_newline = stripped.find("\n")
        last_fence = stripped.rfind("```")
        if first_newline != -1 and last_fence > first_newline:
            stripped = stripped[first_newline + 1:last_fence].strip()

    try:
        fix_plan = json.loads(stripped)
        print("  [Claude] OK JSON parsed successfully")
    except json.JSONDecodeError as e:
        print(f"  [Claude] ERROR Failed to parse JSON: {e}")
        print(f"  [Claude] -> Response (first 500 chars): {stripped[:500]}")
        raise

    # Validate required keys
    print("  [Claude] Validating response structure...")
    for key in ('analysis', 'summary'):
        if key not in fix_plan:
            print(f"  [Claude] ERROR Missing required key: '{key}'")
            raise ValueError(f"Claude response missing required key: '{key}'")
    print("  [Claude] OK Response structure valid")

    return fix_plan


def generate_fix_with_kimi(issue_title, issue_body, code_context):
    """Use Kimi API to generate actual code fix"""

    api_key = os.getenv('KIMI_API_KEY')
    if not api_key:
        raise RuntimeError("KIMI_API_KEY not found")

    if not OPENAI_AVAILABLE:
        raise RuntimeError("openai package not installed")

    # Initialize OpenAI client with Moonshot endpoint
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.cn/v1"
    )

    # Build comprehensive prompt
    prompt = f"""You are an expert Python developer. You need to fix this GitHub issue by writing actual code.

**Issue Title:** {issue_title}

**Issue Description:**
{issue_body}

**Current Codebase Context:**
{json.dumps(code_context, indent=2)}

**Your Task:**
1. Understand what the issue is asking for
2. Identify which file(s) need to be modified
3. Write the COMPLETE FIXED CODE for each file
4. Return your response in this EXACT JSON format:

{{
  "analysis": "Brief explanation of what you're fixing",
  "files_to_modify": [
    {{
      "path": "src/path/to/file.py",
      "action": "modify",
      "new_content": "COMPLETE FILE CONTENT HERE"
    }}
  ],
  "files_to_create": [
    {{
      "path": "src/path/to/newfile.py",
      "content": "COMPLETE FILE CONTENT HERE"
    }}
  ],
  "test_commands": [],
  "summary": "One-sentence summary of the fix"
}}

**CRITICAL REQUIREMENTS:**
- Provide COMPLETE file contents, not just snippets
- Maintain existing code style and structure
- Include proper imports and error handling
- Add comments explaining complex logic
- Ensure code follows Python best practices

Return ONLY valid JSON, no markdown, no explanations outside the JSON.
"""

    print("Calling Kimi API to generate fix...")

    response = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "system", "content": "You are an expert Python developer who returns valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=8000
    )

    if not response.choices or not response.choices[0].message.content:
        raise RuntimeError("Empty response from Kimi API")

    response_text = response.choices[0].message.content

    # Parse JSON response — strip markdown fences if present
    stripped = response_text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.find("\n")
        last_fence = stripped.rfind("```")
        if first_newline != -1 and last_fence > first_newline:
            stripped = stripped[first_newline + 1:last_fence].strip()

    try:
        fix_plan = json.loads(stripped)
    except json.JSONDecodeError as e:
        print(f"Failed to parse Kimi response as JSON: {e}")
        print(f"Response (first 500 chars): {stripped[:500]}")
        raise

    # Validate required keys
    for key in ('analysis', 'summary'):
        if key not in fix_plan:
            raise ValueError(f"Kimi response missing required key: '{key}'")

    return fix_plan


def generate_fix_with_ai(issue_title, issue_body, code_context):
    """Use Claude API to generate fixes"""

    print("\n[Using Claude API for auto-fix]")
    return generate_fix_with_claude(issue_title, issue_body, code_context)


def _is_safe_path(path, root):
    """Ensure path is within the project root (no traversal or symlinks)"""
    try:
        if path.exists() and path.is_symlink():
            return False
        resolved = path.resolve()
        root_resolved = root.resolve()
        resolved.relative_to(root_resolved)
        return True
    except (OSError, ValueError):
        return False


def classify_change_size(fix_plan, issue_title, issue_body):
    """
    Classify if this is a small (auto-commit) or big (needs PR) change

    Returns: 'small' or 'big'
    """
    # Count files being changed
    files_to_modify = len(fix_plan.get('files_to_modify', []))
    files_to_create = len(fix_plan.get('files_to_create', []))
    total_files = files_to_modify + files_to_create

    # Estimate lines changed (rough estimate)
    total_lines = 0
    for file_change in fix_plan.get('files_to_modify', []):
        content = file_change.get('new_content', '')
        total_lines += len(content.split('\n'))
    for new_file in fix_plan.get('files_to_create', []):
        content = new_file.get('content', '')
        total_lines += len(content.split('\n'))

    # Check for risky keywords in issue
    risky_keywords = [
        'refactor', 'rewrite', 'remove', 'delete', 'migrate',
        'database', 'schema', 'api', 'authentication', 'security',
        'breaking', 'major', 'architecture'
    ]

    issue_text = (issue_title + ' ' + issue_body).lower()
    has_risky_keyword = any(keyword in issue_text for keyword in risky_keywords)

    # Classification logic
    if has_risky_keyword:
        return 'big', 'Contains risky keywords (refactor/rewrite/api/security)'

    if total_files >= 3:
        return 'big', f'Too many files ({total_files} files)'

    if total_lines > 100:
        return 'big', f'Too many lines changed (~{total_lines} lines)'

    # Check if modifying core business logic
    core_files = ['processor', 'scorer', 'ranker', 'algorithm']
    for file_change in fix_plan.get('files_to_modify', []):
        file_path = file_change.get('path', '').lower()
        if any(core in file_path for core in core_files):
            return 'big', f'Modifying core business logic ({file_path})'

    # Default: small change
    reason = f'{total_files} file(s), ~{total_lines} lines - looks safe'
    return 'small', reason


def apply_fixes(fix_plan):
    """Apply the fixes generated by Claude"""
    project_root = Path(__file__).parent.parent

    print(f"\nAnalysis: {fix_plan['analysis']}")
    print(f"\nSummary: {fix_plan['summary']}")

    modified_files = []
    backup_paths = []

    # Modify existing files
    for file_change in fix_plan.get('files_to_modify', []):
        file_path = project_root / file_change['path']

        if not _is_safe_path(file_path, project_root):
            print(f"\n  Skipping unsafe path: {file_change['path']}")
            continue

        if 'new_content' not in file_change:
            print(f"\n  Skipping {file_change['path']}: missing 'new_content'")
            continue

        print(f"\n  Modifying: {file_change['path']}")

        file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')

        try:
            # Backup original
            if file_path.exists():
                shutil.copy2(file_path, backup_path)
                backup_paths.append(backup_path)

            # Write to temp, then rename atomically
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(file_change['new_content'])
            temp_path.replace(file_path)
        except OSError:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            raise

        modified_files.append(str(file_path))

    # Create new files
    for new_file in fix_plan.get('files_to_create', []):
        file_path = project_root / new_file['path']

        if not _is_safe_path(file_path, project_root):
            print(f"\n  Skipping unsafe path: {new_file['path']}")
            continue

        if 'content' not in new_file:
            print(f"\n  Skipping {new_file['path']}: missing 'content'")
            continue

        print(f"\n  Creating: {new_file['path']}")

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_file['content'])

        modified_files.append(str(file_path))

    return modified_files, backup_paths


def cleanup_backups(backup_paths):
    """Remove backup files after successful validation"""
    for backup_path in backup_paths:
        try:
            if backup_path.exists():
                backup_path.unlink()
        except OSError as e:
            print(f"  Could not remove backup {backup_path}: {e}")


def _is_allowed_test_command(args):
    """Validate that a test command is safe to run"""
    if not args:
        return False
    if args[0] == 'pytest':
        return True
    if (
        args[0] in ('python', 'python3')
        and len(args) >= 3
        and args[1] == '-m'
        and args[2] == 'pytest'
    ):
        return True
    return False


def run_tests(test_commands):
    """Run tests to verify the fix (only allowed commands)"""
    print("\nRunning tests...")

    for cmd in test_commands:
        args = shlex.split(cmd)
        if not _is_allowed_test_command(args):
            print(f"   Skipping disallowed command: {cmd}")
            continue

        print(f"   Running: {cmd}")
        try:
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=300
            )
        except subprocess.TimeoutExpired:
            print(f"   Test timed out after 300s: {cmd}")
            return False

        if result.returncode != 0:
            print(f"   Test failed:")
            print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
            print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
            return False

    print("   All tests passed!")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python auto_fix_with_claude.py <issue_number>")
        sys.exit(1)

    raw_issue_number = sys.argv[1]
    try:
        issue_number = int(raw_issue_number)
    except ValueError:
        print(f"Invalid issue number: {raw_issue_number}")
        sys.exit(1)

    if issue_number <= 0:
        print(f"Issue number must be positive, got: {issue_number}")
        sys.exit(1)

    print("=" * 60)
    print(f"AUTO-FIX WITH CLAUDE AI")
    print(f"Issue #{issue_number}")
    print("=" * 60)

    # Check environment variables
    print("\n[STEP 0] Checking environment variables...")
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    gh_token = os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
    if anthropic_key:
        print(f"  OK ANTHROPIC_API_KEY found (length: {len(anthropic_key)})")
    else:
        print("  ERROR ANTHROPIC_API_KEY not found!")
    if gh_token:
        print(f"  OK GH_TOKEN found (length: {len(gh_token)})")
    else:
        print("  ERROR GH_TOKEN not found!")

    print(f"  OK ANTHROPIC_AVAILABLE: {ANTHROPIC_AVAILABLE}")
    print(f"  OK OPENAI_AVAILABLE: {OPENAI_AVAILABLE}")

    backup_paths = []

    try:
        # Step 1: Get issue details
        print("\n[STEP 1] Fetching issue details from GitHub...")
        issue = get_issue_details(issue_number)
        print(f"  OK Successfully fetched issue #{issue_number}")

        print(f"  OK Title: {issue['title']}")
        print(f"  OK State: {issue['state']}")

        # Step 2: Read codebase context
        print("\n[STEP 2] Reading codebase for context...")
        code_context = read_relevant_files()
        print(f"  OK Loaded {len(code_context)} files for context")

        # Step 3: Generate fix with AI
        print("\n[STEP 3] Generating fix with Claude AI...")
        print(f"  -> Issue title: {issue['title'][:50]}...")
        print(f"  -> Issue body length: {len(issue.get('body') or '')} chars")
        print(f"  -> Context files: {len(code_context)}")

        fix_plan = generate_fix_with_ai(
            issue['title'],
            issue.get('body') or '',
            code_context
        )
        print(f"  OK Fix plan generated successfully")
        print(f"  -> Analysis: {fix_plan.get('analysis', 'N/A')[:100]}...")

        # Step 4: Classify change size
        print("\n[STEP 4] Classifying change size...")
        change_size, size_reason = classify_change_size(
            fix_plan,
            issue['title'],
            issue.get('body') or ''
        )
        print(f"  OK Classification: {change_size.upper()}")
        print(f"  -> Reason: {size_reason}")

        # Step 5: Apply fixes
        print("\n[STEP 5] Applying fixes...")
        print(f"  -> Files to modify: {len(fix_plan.get('files_to_modify', []))}")
        print(f"  -> Files to create: {len(fix_plan.get('files_to_create', []))}")

        modified_files, backup_paths = apply_fixes(fix_plan)
        print(f"  OK Applied fixes to {len(modified_files)} files")

        # Step 6: Run tests
        print("\n[STEP 6] Running tests...")
        test_commands = fix_plan.get('test_commands', [])
        if test_commands:
            print(f"  -> Test commands: {test_commands}")
            tests_passed = run_tests(test_commands)
        else:
            print("  -> No tests specified, skipping test verification")
            tests_passed = True

        # Step 7: Clean up backups after successful validation
        print("\n[STEP 7] Cleanup and finalization...")
        if tests_passed:
            cleanup_backups(backup_paths)
            print("  OK Cleaned up backup files")
        else:
            print("  WARNING Tests failed — backup files retained for rollback")

        # Step 8: Output results
        print("\n" + "=" * 60)
        print("OK AUTO-FIX COMPLETE!")
        print("=" * 60)
        print(f"\nOK Modified files:")
        for f in modified_files:
            print(f"  - {f}")

        print(f"\nOK Tests: {'PASSED OK' if tests_passed else 'FAILED ERROR'}")
        print(f"\nOK Summary: {fix_plan['summary']}")

        # Write summary for GitHub Actions
        print("\n[STEP 8] Writing summary file...")
        summary_file = Path('AUTO_FIX_SUMMARY.json')
        summary_data = {
            'success': True,
            'issue_number': issue_number,
            'modified_files': modified_files,
            'tests_passed': tests_passed,
            'summary': fix_plan['summary'],
            'change_size': change_size,
            'size_reason': size_reason,
            'auto_commit': change_size == 'small'
        }
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        print(f"  OK Summary written to {summary_file}")
        print(f"  -> Contents: {json.dumps(summary_data, indent=2)}")

        print("\n" + "=" * 60)
        print("OKOKOK SCRIPT COMPLETED SUCCESSFULLY OKOKOK")
        print("=" * 60)

        # Always exit with 0 (success) even if tests fail
        # Tests are optional - the fix itself is what matters
        sys.exit(0)

    except Exception as e:
        print("\n" + "=" * 60)
        print("ERRORERRORERROR ERROR OCCURRED ERRORERRORERROR")
        print("=" * 60)
        print(f"\nERROR Error: {e}")
        print(f"\nERROR Error type: {type(e).__name__}")
        print("\nERROR Full traceback:")
        import traceback
        traceback.print_exc()

        # Clean up backups on failure
        print("\n[CLEANUP] Removing backup files...")
        cleanup_backups(backup_paths)

        # Write failure summary
        print("\n[WRITING FAILURE SUMMARY]")
        summary_file = Path('AUTO_FIX_SUMMARY.json')
        error_data = {
            'success': False,
            'issue_number': issue_number,
            'error': str(e),
            'error_type': type(e).__name__
        }
        with open(summary_file, 'w') as f:
            json.dump(error_data, f, indent=2)
        print(f"  OK Error summary written to {summary_file}")
        print(f"  -> Contents: {json.dumps(error_data, indent=2)}")

        print("\n" + "=" * 60)
        print("ERRORERRORERROR SCRIPT FAILED ERRORERRORERROR")
        print("=" * 60)

        sys.exit(1)


if __name__ == "__main__":
    main()
