#!/usr/bin/env python3
"""
PostToolUseFailure hook: AWS SSO credential auto-renewal.

Detects "Could not load credentials from any providers" errors and automatically
runs `aws sso login --profile X` to refresh expired SSO temporary credentials.

This replicates the behavior of VS Code's AWS Toolkit extension, which auto-triggers
SSO renewal when credentials expire (~1 hour after initial login).

Usage: Add to .claude/settings.json hooks.PostToolUseFailure
"""

import json
import os
import subprocess
import sys
import re

# Read the hook context from stdin
try:
    hook_input = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # Silently pass if no input

# Extract error message from the tool result
error_msg = hook_input.get("result", {}).get("error", "")
if not error_msg:
    sys.exit(0)

# Check if this is an AWS credential error
credential_error_patterns = [
    "Could not load credentials from any providers",
    "Unable to locate credentials",
    "The security token included in the request is expired",
    "ExpiredToken",
    "InvalidClientTokenId",
]

is_credential_error = any(pattern in error_msg for pattern in credential_error_patterns)
if not is_credential_error:
    sys.exit(0)

# Determine which AWS profile is being used
# Priority: AWS_PROFILE env var > settings.json env.AWS_PROFILE > default profile
aws_profile = os.environ.get("AWS_PROFILE")

if not aws_profile:
    # Try to read from project settings.json
    try:
        settings_path = os.path.join(os.getcwd(), ".claude", "settings.json")
        if os.path.exists(settings_path):
            with open(settings_path) as f:
                settings = json.load(f)
                aws_profile = settings.get("env", {}).get("AWS_PROFILE")
    except Exception:
        pass

if not aws_profile:
    # Try to extract profile name from error message
    profile_match = re.search(r"profile[:\s]+([a-zA-Z0-9_-]+)", error_msg)
    if profile_match:
        aws_profile = profile_match.group(1)

if not aws_profile:
    # Fall back to a sensible default based on repo
    repo_name = os.path.basename(os.getcwd()).lower()
    if "100eggs" in repo_name or "eggs-ai-ops" in repo_name:
        aws_profile = "100eggs-admin"
    else:
        aws_profile = "Admin-351596828163"

# Attempt SSO login
try:
    result = subprocess.run(
        ["aws", "sso", "login", "--profile", aws_profile],
        capture_output=True,
        text=True,
        timeout=90,  # Give user time to approve MFA
    )

    if result.returncode == 0:
        # Success - tell Claude to retry the tool call
        msg = {
            "systemMessage": f"AWS SSO credentials refreshed for profile '{aws_profile}'. Browser opened for MFA approval. Retry the failed AWS tool call now."
        }
        print(json.dumps(msg))
    else:
        # Login failed - surface the error but don't block
        msg = {
            "systemMessage": f"AWS SSO login failed for profile '{aws_profile}': {result.stderr.strip()[:200]}. Run `aws sso login --profile {aws_profile}` manually."
        }
        print(json.dumps(msg))

except subprocess.TimeoutExpired:
    msg = {
        "systemMessage": f"AWS SSO login timed out waiting for MFA approval. Complete the browser flow manually or run `aws sso login --profile {aws_profile}`."
    }
    print(json.dumps(msg))
except Exception as e:
    msg = {
        "systemMessage": f"AWS SSO auto-renewal failed: {str(e)[:200]}. Run `aws sso login --profile {aws_profile}` manually."
    }
    print(json.dumps(msg))
