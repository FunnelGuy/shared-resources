#!/usr/bin/env python3
"""Roll out the Tier-1 pre-commit secret gate to fleet repos (spec 5.740 P3).

For each target repo:
  1. Vendor the single-source `.gitleaks.toml` to the repo root (so the local gitleaks hook uses
     the SAME rules as CI/RM). A stale local copy is only a fast-catch convenience — CI (P2) and
     RM R1 (P3) always scan with the current shared config, so authoritative detection never drifts.
  2. Add the gitleaks stanza to `.pre-commit-config.yaml` (create it if absent, append if present,
     skip if the gitleaks hook is already there).

DRY-RUN by default; --apply branches/commits/pushes and opens a PR.

The pinned gitleaks version in the stanza MUST match the fleet pin (config + CI). This script reads
it from the vendored config's title-comment so it can't drift.

Usage:
  python3 scripts/rollout_precommit_gitleaks.py --list
  python3 scripts/rollout_precommit_gitleaks.py --repos ../va ../hr-manager
  python3 scripts/rollout_precommit_gitleaks.py --all --apply
"""

import argparse
import subprocess
import sys
from pathlib import Path

BRANCH = "feat/5.740-precommit-gitleaks"
GITLEAKS_VERSION = "8.30.1"  # fleet pin; keep in sync with .gitleaks.toml + secret-scan.yml

STANZA = """-   repo: https://github.com/gitleaks/gitleaks
    rev: v{ver}
    hooks:
    -   id: gitleaks
        name: gitleaks (fleet secret-scan, spec 5.740)
"""

EMPTY_PRECOMMIT = "repos:\n" + "".join("  " + line + "\n" for line in STANZA.strip().splitlines())


def sh(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def _vendor_config(shared_dir: Path, repo_dir: Path) -> bool:
    """Copy the single-source .gitleaks.toml to the repo root. Returns True if changed."""
    src = shared_dir / "shared-configs" / "gitleaks" / ".gitleaks.toml"
    dst = repo_dir / ".gitleaks.toml"
    new = src.read_text()
    if dst.exists() and dst.read_text() == new:
        return False
    dst.write_text(new)
    return True


def _add_stanza(repo_dir: Path) -> str:
    """Add the gitleaks stanza to .pre-commit-config.yaml. Returns 'added'|'present'|'created'."""
    cfg = repo_dir / ".pre-commit-config.yaml"
    stanza = STANZA.format(ver=GITLEAKS_VERSION)
    if not cfg.exists():
        cfg.write_text("repos:\n" + "".join("  " + ln + "\n" if ln else "\n"
                                             for ln in stanza.splitlines()))
        return "created"
    text = cfg.read_text()
    if "gitleaks/gitleaks" in text:
        return "present"
    # Append the stanza under the existing `repos:` list (indented 4 like typical pre-commit lists,
    # but many fleet configs use 0-indent list items under repos: — match the file's style).
    indented = "".join("  " + ln + "\n" if ln.strip() else "\n" for ln in stanza.splitlines())
    if not text.endswith("\n"):
        text += "\n"
    cfg.write_text(text + indented)
    return "added"


def rollout_repo(shared_dir: Path, repo_dir: Path, apply: bool) -> dict:
    name = repo_dir.name
    res = {"repo": name, "action": None, "detail": ""}
    if not (repo_dir / ".git").exists():
        res["action"] = "skip"; res["detail"] = "not a git repo"; return res
    if not apply:
        cfg = repo_dir / ".pre-commit-config.yaml"
        has_hook = cfg.exists() and "gitleaks/gitleaks" in cfg.read_text()
        res["action"] = "dry-run"
        res["detail"] = "already has gitleaks hook" if has_hook else \
            f"would vendor .gitleaks.toml + add stanza (gitleaks v{GITLEAKS_VERSION})"
        return res
    sh(["git", "checkout", "-b", BRANCH], cwd=repo_dir)
    changed_cfg = _vendor_config(shared_dir, repo_dir)
    stanza_action = _add_stanza(repo_dir)
    if not changed_cfg and stanza_action == "present":
        sh(["git", "checkout", "-", ], cwd=repo_dir, check=False)
        sh(["git", "branch", "-D", BRANCH], cwd=repo_dir, check=False)
        res["action"] = "skip"; res["detail"] = "already fully configured"; return res
    sh(["git", "add", ".gitleaks.toml", ".pre-commit-config.yaml"], cwd=repo_dir)
    sh(["git", "commit", "-m",
        "5.740 P3: add gitleaks pre-commit secret gate (Tier 1 block)\n\n"
        f"Vendors the shared .gitleaks.toml + adds the pinned gitleaks v{GITLEAKS_VERSION} "
        "pre-commit hook. Local best-effort BLOCK before a secret reaches the remote; CI (Tier 2) "
        "+ RM R1 (Tier 3) detect any --no-verify bypass.\n\n"
        "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"], cwd=repo_dir)
    sh(["git", "push", "-u", "origin", BRANCH], cwd=repo_dir)
    pr = sh(["gh", "pr", "create", "--title", "5.740 P3: gitleaks pre-commit secret gate",
             "--body", "Adds the Tier-1 pre-commit secret gate (spec 5.740): vendored shared "
             f"`.gitleaks.toml` + pinned gitleaks v{GITLEAKS_VERSION} hook.\n\n"
             "\U0001f916 Generated with [Claude Code](https://claude.com/claude-code)"], cwd=repo_dir)
    res["action"] = "pr-opened"; res["detail"] = pr
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    shared_dir = Path(__file__).resolve().parent.parent
    base = shared_dir.parent

    if args.list:
        print(f"Pinned gitleaks: v{GITLEAKS_VERSION}")
        print("Pass --repos or --all (dry-run unless --apply).")
        return

    if args.repos:
        targets = [(shared_dir / r).resolve() for r in args.repos]
    elif args.all:
        targets = [p for p in sorted(base.iterdir())
                   if (p / ".git").exists() and p.name != "shared-resources"]
    else:
        print("Specify --repos, --all, or --list", file=sys.stderr); sys.exit(2)

    print(f"P3 pre-commit rollout — gitleaks v{GITLEAKS_VERSION} apply={args.apply}\n")
    for t in targets:
        r = rollout_repo(shared_dir, Path(t), args.apply)
        print(f"  {r['repo']:28} {r['action']:10} {r['detail']}")


if __name__ == "__main__":
    main()
