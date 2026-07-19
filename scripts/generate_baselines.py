#!/usr/bin/env python3
"""Generate per-repo gitleaks baselines at adoption (spec 5.740 P5).

A baseline is a JSON list of findings that gitleaks then treats as already-accepted, so the
Tier-1/Tier-2 gates do NOT wall off commits on day one for pre-existing findings (mostly the
benign drive-ID / Exchange-ID / Sheets-ID fragments deferred here from the rule-tuning). It
writes `.gitleaks-baseline.json` at each repo root; the caller CI workflow reads it via
`baseline_path`.

A baseline MUTES a known match; it can NEVER permanently exempt a real secret: RM R1 re-scans
baselined entries every week and re-flags any that still resolve live (spec pattern #8 mechanism).
So a genuine secret accidentally baselined is caught on the next weekly RM run.

IMPORTANT: review each baseline before committing. If the current findings include a REAL secret
(as the KM/Co-CEO scans did), do NOT baseline it — rotate + scrub it first. Baseline only the
confirmed-benign residual.

Usage:
  python3 scripts/generate_baselines.py --repos ../va                # dry-run: show what would baseline
  python3 scripts/generate_baselines.py --repos ../va --write        # write .gitleaks-baseline.json
  python3 scripts/generate_baselines.py --all --write
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def _config(shared_dir: Path) -> str:
    return str(shared_dir / "shared-configs" / "gitleaks" / ".gitleaks.toml")


# Rules that indicate a GENUINE credential — never auto-baseline these; they must be rotated.
_NEVER_BASELINE_RULES = {
    "private-key", "aws-access-token", "aws-secret-key", "gcp-api-key", "github-pat",
    "slack-token", "stripe-access-token", "azure-ad-client-secret",
}
# Files that should never be baselined (a secret here is real by construction).
_NEVER_BASELINE_FILE_MARKERS = (".mcp.json", ".key", ".pfx", ".pem", "credentials")


def scan_head(repo_dir: Path, config: str) -> list[dict]:
    """Scan the repo's COMMITTED content (HEAD), producing RELATIVE-path fingerprints.

    Two correctness requirements the baseline depends on (both learned the hard way, 5.740 rollout):
      1. RELATIVE fingerprints. gitleaks' dir-mode Fingerprint is `<path>:<rule>:<line>`. If we scan
         by absolute path, the fingerprint carries the local abs path and will NEVER match a CI run
         (which does `gitleaks dir .` in a checkout → relative paths). So we `git archive` HEAD into a
         temp dir and run gitleaks with cwd=that dir scanning `.` — identical to what CI sees.
      2. COMMITTED content only. Scanning the live working tree pulls in gitignored files (.mcp.json,
         sp-credentials.json) that CI never sees — polluting the baseline with entries that can't
         match and, worse, listing real local secrets in a committed baseline file. git archive
         excludes anything not committed.
    """
    import json
    default = subprocess.run(["git", "-C", str(repo_dir), "symbolic-ref", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip() or "HEAD"
    with tempfile.TemporaryDirectory(prefix="baseline-") as tree:
        arch = subprocess.run(f"git -C {repo_dir} archive {default} | tar -x -C {tree}",
                              shell=True, capture_output=True, text=True)
        if arch.returncode != 0:
            raise RuntimeError(f"git archive failed: {arch.stderr.strip()[:200]}")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as rep:
            report = rep.name
        try:
            proc = subprocess.run(
                ["gitleaks", "dir", ".", "--config", config,
                 "--report-format", "json", "--report-path", report,
                 "--no-banner", "--exit-code", "0"],
                cwd=tree, capture_output=True, text=True, timeout=600)
            if proc.returncode != 0:
                raise RuntimeError(f"gitleaks failed (rc={proc.returncode}): {proc.stderr.strip()[:200]}")
            with open(report) as fh:
                return json.load(fh)
        finally:
            Path(report).unlink(missing_ok=True)


def partition(findings: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split into (baseline-eligible benign, must-remediate genuine)."""
    benign, genuine = [], []
    for f in findings:
        rule = f.get("RuleID", "")
        fpath = (f.get("File") or "").lower()
        is_genuine = rule in _NEVER_BASELINE_RULES or any(m in fpath for m in _NEVER_BASELINE_FILE_MARKERS)
        (genuine if is_genuine else benign).append(f)
    return benign, genuine


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--write", action="store_true", help="write .gitleaks-baseline.json")
    ap.add_argument("--include-genuine", action="store_true",
                    help="also baseline the genuine-classified COMMITTED findings (only after each "
                         "has been manually verified benign/already-rotated — makes CI green when the "
                         "residual is confirmed non-live; the genuine list is always printed either way)")
    args = ap.parse_args()

    import json
    shared_dir = Path(__file__).resolve().parent.parent
    base = shared_dir.parent
    config = _config(shared_dir)

    if args.repos:
        targets = [(shared_dir / r).resolve() for r in args.repos]
    elif args.all:
        targets = [p for p in sorted(base.iterdir()) if (p / ".git").exists()]
    else:
        print("Specify --repos or --all", file=sys.stderr); sys.exit(2)

    print(f"P5 baseline generation — write={args.write} include_genuine={args.include_genuine}\n")
    for t in targets:
        t = Path(t)
        try:
            findings = scan_head(t, config)
        except Exception as exc:  # noqa: BLE001
            print(f"  {t.name:28} ERROR {exc}")
            continue
        benign, genuine = partition(findings)
        to_write = benign + genuine if args.include_genuine else benign
        flag = f"  <-- {len(genuine)} genuine{' (INCLUDED)' if args.include_genuine else ' (excluded — CI stays red until verified/scrubbed)'}" if genuine else ""
        print(f"  {t.name:28} {len(benign):4d} benign / {len(genuine):3d} genuine{flag}")
        for g in genuine:
            print(f"        genuine: {g.get('RuleID')} {g.get('File')}:{g.get('StartLine')}")
        if args.write:
            if to_write:
                (t / ".gitleaks-baseline.json").write_text(json.dumps(to_write, indent=2))
                print(f"      wrote {t.name}/.gitleaks-baseline.json ({len(to_write)} entries)")
            else:
                # No committed findings: ensure no stale baseline lingers.
                (t / ".gitleaks-baseline.json").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
