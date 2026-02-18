# Branch Protocols

Universal branch creation and management protocols for all align.me repos.

## Branch creation is mandatory

**Before making any file changes:**

1. **Pull latest:** `git pull`
2. **Create branch:** `git checkout -b [branch-name]`
3. **Create branch guide** in `branch_guides/` using the template
4. **Then start coding** — never modify files on the main branch

**Zero tolerance.** If you catch yourself working on main, stop immediately, create a branch, and move the changes.

## Branch naming convention

```
[version]-[type]-[domain]-[description]
```

- **Version:** Dash-separated (e.g. `15-3-10` not `15.3.10`)
- **Type:** `bugfix` | `feature` | `refactor` | `admin` | `hotfix`
- **Domain:** From the repo's domain list (see repo CLAUDE.md or DEVELOPMENT_PROTOCOLS.md)
- **Description:** Specific, not generic

**Examples:**
- `15-3-10-bugfix-extraction-scroll-failure`
- `15-5-0-feature-automation-withdraw-invitations`
- `2-1-0-feature-api-calendar-integration`

## Version calculation

Determine target version based on work type:

- **PATCH** (x.x.+1): Bug fixes, documentation updates
- **MINOR** (x.+1.0): New features, backwards compatible
- **MAJOR** (+1.0.0): Breaking changes or major features

Always verify the target version with the user before starting work.

## Branch closure

When the user requests to close out a branch:

1. **Verify readiness** — all success criteria met, all files tested
2. **Pull latest** — `git pull`, resolve any conflicts
3. **Update branch guide** — mark complete, add final status
4. **Clean up** — remove test files, update version and changelog
5. **Push** — `git push -u origin [branch-name]`
6. **Merge** — switch to main, pull, merge with `--no-ff`, push
7. **Delete branch** — local and remote

## Hotfix protocol

For critical production issues:

1. Create a hotfix branch (never commit directly to main)
2. Fix and build a test version on the branch
3. Deliver to user for testing — **wait for confirmation**
4. Only merge to main after explicit user approval
5. Never push untested code to main

## Protocol violations

If you violate any protocol:

1. **Stop** immediately
2. **Acknowledge** the specific violation
3. **Correct** — create the branch, read the file, fix the date
4. **Document** the violation and recovery in the branch guide
