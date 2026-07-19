#!/usr/bin/env python3
"""Roll out the Tier-2 secret-scan caller workflow to fleet repos (spec 5.740 P2).

For each target repo: create a branch, add `.github/workflows/secret-scan.yml` (the caller,
pinned to a real shared-resources SHA), commit, push, open a PR. Scriptable per fleet-pattern
#17 (one SHA bump updates the tenant). DRY-RUN by default; --apply actually pushes/opens PRs.

The caller is pinned to a real COMMIT SHA (never a branch/tag) so the gate's behaviour cannot
change under a repo without review.

Usage:
  python3 scripts/rollout_secret_scan.py --list                      # show target repos + resolved SHA
  python3 scripts/rollout_secret_scan.py --repos ../va ../hr-manager # dry-run for specific repos
  python3 scripts/rollout_secret_scan.py --all --apply               # roll out to all, open PRs
  python3 scripts/rollout_secret_scan.py --all --sha <sha>           # pin a specific shared-resources SHA
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Tenant-agnostic: the shared repo that hosts the reusable workflow. For 100eggs, pass
# --shared-repo eggs-org/shared-protocols (its own tenant copy).
DEFAULT_SHARED_REPO = "FunnelGuy/shared-resources"

CALLER_PATH = ".github/workflows/secret-scan.yml"
BRANCH = "feat/5.740-secret-scan-caller"

CALLER_TEMPLATE = """name: Secret scan

on:
  push:
  pull_request:

jobs:
  secret-scan:
    uses: {shared_repo}/.github/workflows/secret-scan.yml@{sha}
"""


def sh(cmd: list[str], cwd: str | None = None, check: bool = True) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def resolve_shared_sha(shared_dir: str) -> str:
    """The current HEAD SHA of shared-resources main — the SHA callers pin to. Callers must pin
    to a MERGED SHA on the default branch (not the feature branch), so run this after the P2 PR
    merges. Until then it returns the feature-branch tip for dry-run preview only."""
    return sh(["git", "rev-parse", "HEAD"], cwd=shared_dir)


def rollout_repo(repo_dir: str, shared_repo: str, sha: str, apply: bool) -> dict:
    name = Path(repo_dir).name
    result = {"repo": name, "action": None, "detail": ""}
    if not (Path(repo_dir) / ".git").exists():
        result["action"] = "skip"
        result["detail"] = "not a git repo"
        return result
    caller = Path(repo_dir) / CALLER_PATH
    if caller.exists():
        result["action"] = "skip"
        result["detail"] = "caller already present"
        return result
    content = CALLER_TEMPLATE.format(shared_repo=shared_repo, sha=sha)
    if not apply:
        result["action"] = "dry-run"
        result["detail"] = f"would add {CALLER_PATH} pinned @ {sha[:8]}"
        return result
    # apply: branch, write, commit, push, PR
    sh(["git", "checkout", "-b", BRANCH], cwd=repo_dir)
    caller.parent.mkdir(parents=True, exist_ok=True)
    caller.write_text(content)
    sh(["git", "add", CALLER_PATH], cwd=repo_dir)
    sh(["git", "commit", "-m",
        "5.740 P2: add Tier-2 secret-scan CI caller\n\n"
        f"Calls the fleet reusable secret-scan workflow at pinned SHA {sha[:8]}.\n"
        "Detection backstop (post-push) for secrets that bypass the pre-commit hook.\n\n"
        "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"], cwd=repo_dir)
    sh(["git", "push", "-u", "origin", BRANCH], cwd=repo_dir)
    pr_url = sh(["gh", "pr", "create", "--title", "5.740 P2: add secret-scan CI caller",
                 "--body", "Adds the Tier-2 secret-scan CI detection job (spec 5.740). "
                 f"Calls the fleet reusable workflow at pinned SHA `{sha[:8]}`.\n\n"
                 "🤖 Generated with [Claude Code](https://claude.com/claude-code)"], cwd=repo_dir)
    result["action"] = "pr-opened"
    result["detail"] = pr_url
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="*", help="specific repo dirs (relative to shared-resources)")
    ap.add_argument("--all", action="store_true", help="all repos in the sync table")
    ap.add_argument("--shared-repo", default=DEFAULT_SHARED_REPO)
    ap.add_argument("--sha", help="pin this shared-resources SHA (default: current HEAD)")
    ap.add_argument("--apply", action="store_true", help="actually push + open PRs")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent.parent  # shared-resources/
    sha = args.sha or resolve_shared_sha(str(here))

    if args.list:
        print(f"Shared repo: {args.shared_repo}")
        print(f"Pinned SHA:  {sha}")
        print("Pass --repos or --all to roll out (dry-run unless --apply).")
        return

    if args.repos:
        targets = [str((here / r).resolve()) for r in args.repos]
    elif args.all:
        # Read the HoAO repo-sync-table for the tenant's own repo universe.
        targets = []
        base = here.parent  # align.me/
        for p in sorted(base.iterdir()):
            if (p / ".git").exists() and p.name != "shared-resources":
                targets.append(str(p))
    else:
        print("Specify --repos, --all, or --list", file=sys.stderr)
        sys.exit(2)

    print(f"Rollout — shared={args.shared_repo} sha={sha[:8]} apply={args.apply}\n")
    for t in targets:
        r = rollout_repo(t, args.shared_repo, sha, args.apply)
        print(f"  {r['repo']:28} {r['action']:10} {r['detail']}")


if __name__ == "__main__":
    main()
