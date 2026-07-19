#!/usr/bin/env python3
"""One-off git-HISTORY secret backfill scan (spec 5.740 P4, Tier 4).

The ONLY tier that finds secrets ALREADY in git history — the exact KM failure class. Runs
`gitleaks git` (full-history patch scan) over each repo with the shared `.gitleaks.toml`. This
needs git + local disk, so it runs on a CI runner or a dev box (NOT the RM Lambda, which has
neither). Produces a per-repo triage report: for each historical hit, the rule, file, commit,
and a sha256 prefix of the secret (never the raw value).

Findings here are REMEDIATED by rotation + history scrub (git filter-repo), per the KM
remediation playbook — not by baselining (a baseline hides a live secret).

Usage:
  python3 scripts/history_backfill_scan.py --repos ../va ../Co-CEO      # scan specific repos
  python3 scripts/history_backfill_scan.py --all                         # scan the whole fleet
  python3 scripts/history_backfill_scan.py --all --json report.json      # machine-readable out
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _config_path(shared_dir: Path) -> str:
    return str(shared_dir / "shared-configs" / "gitleaks" / ".gitleaks.toml")


def scan_history(repo_dir: Path, config: str) -> list[dict]:
    """Run gitleaks git-history scan. Returns parsed findings (raw secret dropped)."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as rep:
        report = rep.name
    try:
        proc = subprocess.run(
            ["gitleaks", "git", str(repo_dir), "--config", config,
             "--report-format", "json", "--report-path", report,
             "--no-banner", "--exit-code", "0"],
            capture_output=True, text=True, timeout=1800,
        )
        if proc.returncode != 0:
            # config-load / engine failure -> surface, do not silently pass
            raise RuntimeError(f"gitleaks git failed (rc={proc.returncode}): {proc.stderr.strip()[:300]}")
        with open(report) as fh:
            raw = json.load(fh)
    finally:
        Path(report).unlink(missing_ok=True)
    out = []
    for h in raw:
        secret = h.get("Secret", "")
        out.append({
            "rule": h.get("RuleID"),
            "file": h.get("File"),
            "commit": (h.get("Commit") or "")[:12],
            "date": h.get("Date"),
            "author": h.get("Author"),
            "line": h.get("StartLine"),
            "secret_sha256_12": hashlib.sha256(secret.encode()).hexdigest()[:12],
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", help="write full machine-readable report to this path")
    args = ap.parse_args()

    shared_dir = Path(__file__).resolve().parent.parent
    base = shared_dir.parent
    config = _config_path(shared_dir)

    if args.repos:
        targets = [(shared_dir / r).resolve() for r in args.repos]
    elif args.all:
        targets = [p for p in sorted(base.iterdir()) if (p / ".git").exists()]
    else:
        print("Specify --repos or --all", file=sys.stderr); sys.exit(2)

    report = {}
    print(f"P4 history backfill — config {Path(config).name}\n")
    for t in targets:
        t = Path(t)
        try:
            hits = scan_history(t, config)
        except Exception as exc:  # noqa: BLE001
            print(f"  {t.name:28} ERROR   {exc}")
            report[t.name] = {"error": str(exc)}
            continue
        # dedup by (rule, file, secret hash) — history repeats the same secret across commits
        uniq = {(h["rule"], h["file"], h["secret_sha256_12"]): h for h in hits}
        report[t.name] = {"total_hits": len(hits), "distinct_secrets": len(uniq),
                          "findings": list(uniq.values())}
        flag = "  <-- REVIEW" if uniq else ""
        print(f"  {t.name:28} {len(uniq):4d} distinct historical secrets ({len(hits)} raw hits){flag}")

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
        print(f"\nFull report -> {args.json}")


if __name__ == "__main__":
    main()
