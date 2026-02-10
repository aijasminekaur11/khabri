"""
Claude Auto-Fixer
Uses Claude API to automatically analyze and fix GitHub issues
"""

import os
import logging
from typing import Dict, Any, Optional, List
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeAutoFixer:
    """
    Uses Claude API to automatically fix issues
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude Auto-Fixer

        Args:
            api_key: Anthropic API key (defaults to env ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

        if not self.api_key:
            logger.warning("Anthropic API key not configured. Auto-fix disabled.")
            logger.warning(f"Checked environment variable: ANTHROPIC_API_KEY = {os.getenv('ANTHROPIC_API_KEY')}")
            self.client = None
        else:
            logger.info(f"Claude API initialized with key: {self.api_key[:20]}...")
            self.client = Anthropic(api_key=self.api_key)

    def analyze_issue(self, issue_title: str, issue_body: str, repo_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze an issue and generate a fix plan

        Args:
            issue_title: Title of the issue
            issue_body: Description of the issue
            repo_context: Optional repository context (files, structure, etc.)

        Returns:
            Dict with analysis and fix plan
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Claude API not configured',
                'message': 'Set ANTHROPIC_API_KEY to enable auto-fix'
            }

        try:
            # Build the prompt
            prompt = f"""You are an expert software engineer. Analyze this issue and provide a fix plan.

**Issue Title:** {issue_title}

**Issue Description:**
{issue_body}

**Your Task:**
1. Understand what the issue is asking for
2. Identify the root cause or required changes
3. Provide a step-by-step fix plan
4. Suggest specific code changes if applicable

**Output Format:**
Provide your analysis in this format:

## Understanding
[What is the issue about?]

## Root Cause
[What needs to be fixed or added?]

## Fix Plan
1. [Step 1]
2. [Step 2]
...

## Suggested Changes
[Specific code changes, file locations, etc.]

Be concise but thorough."""

            # Call Claude API
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Latest Sonnet model
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = message.content[0].text

            return {
                'success': True,
                'analysis': analysis,
                'model': 'claude-sonnet-4',
                'tokens_used': message.usage.input_tokens + message.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to analyze issue with Claude'
            }

    def generate_code_fix(
        self,
        issue_description: str,
        file_content: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Generate actual code fix for a specific file

        Args:
            issue_description: What needs to be fixed
            file_content: Current content of the file
            file_path: Path to the file

        Returns:
            Dict with fixed code
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Claude API not configured'
            }

        try:
            prompt = f"""Fix this code based on the issue description.

**Issue:** {issue_description}

**File:** {file_path}

**Current Code:**
```
{file_content}
```

**Instructions:**
1. Fix the code to resolve the issue
2. Maintain existing code style
3. Add comments where helpful
4. Return ONLY the fixed code, no explanations

Return the complete fixed file content."""

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            fixed_code = message.content[0].text

            # Clean up markdown code blocks if present
            if fixed_code.startswith("```"):
                lines = fixed_code.split("\n")
                # Remove first line (```) and last line (```)
                fixed_code = "\n".join(lines[1:-1])

            return {
                'success': True,
                'fixed_code': fixed_code,
                'tokens_used': message.usage.input_tokens + message.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"Claude API error generating fix: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_fix_summary(self, issue_title: str, analysis: str) -> str:
        """
        Generate a concise summary of the fix for PR description

        Args:
            issue_title: Title of the issue
            analysis: Full analysis from Claude

        Returns:
            Markdown-formatted PR description
        """
        if not self.client:
            return f"## Auto-Fix\n\nAttempted to fix: {issue_title}\n\nClaude API not configured."

        try:
            prompt = f"""Create a concise PR description (max 200 words) for this fix.

**Issue:** {issue_title}

**Analysis:**
{analysis}

Format as:
## Fix Summary
[2-3 sentences about what was fixed]

## Changes Made
- [Change 1]
- [Change 2]

Keep it brief and professional."""

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"## Auto-Fix\n\nAttempted to fix: {issue_title}"
