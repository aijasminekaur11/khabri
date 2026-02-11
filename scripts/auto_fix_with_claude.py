#!/usr/bin/env python3
"""
Auto-Fix Script with Claude API
Automatically fixes GitHub issues using Claude AI to write code
"""

import os
import sys
import json
import subprocess
import shlex
import shutil
from pathlib import Path

from anthropic import Anthropic


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


def generate_fix_with_claude(issue_title, issue_body, code_context):
    """Use Claude API to generate actual code fix"""

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not found")

    client = Anthropic(api_key=api_key)

    # Build comprehensive prompt for Claude
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
  "test_commands": ["pytest testing/test_cases/...", "..."],
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

    print("Calling Claude API to generate fix...")

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    if not message.content:
        raise RuntimeError("Empty response from Claude API")
    response_text = message.content[0].text

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
        print(f"Failed to parse Claude response as JSON: {e}")
        print(f"Response (first 500 chars): {stripped[:500]}")
        raise

    # Validate required keys
    for key in ('analysis', 'summary'):
        if key not in fix_plan:
            raise ValueError(f"Claude response missing required key: '{key}'")

    return fix_plan


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

    backup_paths = []

    try:
        # Step 1: Get issue details
        print("\nFetching issue details from GitHub...")
        issue = get_issue_details(issue_number)

        print(f"   Title: {issue['title']}")
        print(f"   State: {issue['state']}")

        # Step 2: Read codebase context
        print("\nReading codebase for context...")
        code_context = read_relevant_files()
        print(f"   Loaded {len(code_context)} files for context")

        # Step 3: Generate fix with Claude
        print("\nGenerating fix with Claude AI...")
        fix_plan = generate_fix_with_claude(
            issue['title'],
            issue.get('body') or '',
            code_context
        )

        # Step 4: Apply fixes
        print("\nApplying fixes...")
        modified_files, backup_paths = apply_fixes(fix_plan)

        # Step 5: Run tests
        test_commands = fix_plan.get('test_commands', [])
        if test_commands:
            tests_passed = run_tests(test_commands)
        else:
            print("\nNo tests specified, skipping test verification")
            tests_passed = True

        # Step 5b: Clean up backups after successful validation
        if tests_passed:
            cleanup_backups(backup_paths)
        else:
            print("\nTests failed — backup files retained for rollback")

        # Step 6: Output results
        print("\n" + "=" * 60)
        print("AUTO-FIX COMPLETE!")
        print("=" * 60)
        print(f"\nModified files:")
        for f in modified_files:
            print(f"  - {f}")

        print(f"\nTests: {'Passed' if tests_passed else 'Failed'}")
        print(f"\nSummary: {fix_plan['summary']}")

        # Write summary for GitHub Actions
        summary_file = Path('AUTO_FIX_SUMMARY.json')
        with open(summary_file, 'w') as f:
            json.dump({
                'success': True,
                'issue_number': issue_number,
                'modified_files': modified_files,
                'tests_passed': tests_passed,
                'summary': fix_plan['summary']
            }, f, indent=2)

        sys.exit(0 if tests_passed else 1)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

        # Clean up backups on failure
        cleanup_backups(backup_paths)

        # Write failure summary
        summary_file = Path('AUTO_FIX_SUMMARY.json')
        with open(summary_file, 'w') as f:
            json.dump({
                'success': False,
                'issue_number': issue_number,
                'error': str(e)
            }, f, indent=2)

        sys.exit(1)


if __name__ == "__main__":
    main()
