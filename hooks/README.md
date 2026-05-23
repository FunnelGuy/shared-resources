# Fleet-wide Claude Code hooks

Shared hooks for all align.me agent repos. Referenced by `.claude/settings.json` in each agent repo via relative path.

## aws_sso_renewal_hook.py

**Purpose:** Automatically refresh AWS SSO credentials when they expire (~1 hour after initial login).

**Trigger:** PostToolUseFailure hook — fires when any tool call fails.

**Behavior:**
1. Detects AWS credential errors ("Could not load credentials from any providers", "ExpiredToken", etc.)
2. Determines the active AWS profile from `AWS_PROFILE` env var or `.claude/settings.json`
3. Runs `aws sso login --profile X` to refresh credentials
4. Opens default browser for MFA approval
5. Returns a systemMessage telling Claude to retry the failed tool call

**Why this exists:** SSO temporary credentials expire ~1 hour after initial login. Without this hook, every agent session would error with "Could not load credentials" and require manual `aws sso login` intervention. This hook replicates the behavior of VS Code's AWS Toolkit extension (which auto-triggers SSO renewal on Hugh's PC).

**Requirements:**
- All profiles in `~/.aws/config` must be SSO-linked (include `sso_session`, `sso_account_id`, `sso_role_name` fields)
- Chrome set as default browser (for SSO login flow)
- AWS CLI installed (`aws` command available in PATH)

**Deployment status:** Deployed 2026-05-23 to all 25 align.me agent repos via PostToolUseFailure hook in each `.claude/settings.json`.

**Testing:** Run any AWS CLI command with expired credentials. The hook should detect the error, open a browser for SSO login, and tell Claude to retry.

**Maintenance:** When updating this hook, commit to `shared-resources/hooks/` only. All agent repos reference this shared copy via relative path `../shared-resources/hooks/aws_sso_renewal_hook.py`. No need to update 25 individual repos.

## Adding a new shared hook

1. Write the hook script in this directory
2. Make it executable (`chmod +x hook-name.py`)
3. Add to all agent repos' `.claude/settings.json` via the fleet-wide update script in `head-of-ai-operations/temp/` (see `add_sso_hook_to_all_repos.py` as a template)
4. Document here in this README
5. Test in at least one agent repo before deploying fleet-wide
