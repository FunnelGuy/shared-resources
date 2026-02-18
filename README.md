# Shared Resources

Centralised shared resources for all align.me GitHub repos. This repo was renamed from `common-runtime-resources` to `shared-resources` on 2026-02-18 to better reflect its expanded scope.

## Purpose

This repository holds resources that are shared across all repos on this machine:

- **Claude Code guardrails** — ThreatLocker PreToolUse hook (blocks script creation/execution outside GitHub folders)
- **Development protocols** — branch naming, versioning, session management, branch guide templates
- **Shared configurations** — AWS regions, endpoints, deployment configs
- **Credential templates** — placeholder files for sensitive credentials (actual credentials are gitignored)

## Repository Structure

```
shared-resources/
├── README.md                          # This file
├── .gitignore                         # Excludes sensitive files
├── claude-hooks/
│   └── threatlocker-guard.py          # Canonical PreToolUse hook (all repos)
├── dev-protocols/
│   ├── README.md                      # What's shared vs. repo-specific
│   ├── BRANCH_PROTOCOLS.md            # Branch creation, naming, versioning, closure
│   ├── INSTRUCTIONS_FOR_CLAUDE.md     # Claude Code session guidelines
│   └── BRANCH_GUIDE_TEMPLATE.md       # Universal branch guide template
├── shared-configs/
│   ├── regions.json                   # AWS regions and defaults
│   ├── endpoints.json                 # API endpoints and URLs
│   └── aws-lambda-deployment.json     # Lambda deployment config
└── templates/
    ├── credentials.template.txt       # AWS credential placeholder
    └── boto3-usage-examples.py        # AWS SDK usage reference
```

## Three-Tier Shared Standards

All align.me repos inherit standards from three levels:

```
~/.claude/CLAUDE.md              (Tier 1 — user-level, all repos automatically)
    ↓ contains: ThreatLocker, locale, company values, brand standards,
      Knowledge Manager authority, Content Agent Request template

shared-resources/                (Tier 2 — shared repo, referenced by path)
    ↓ contains: hook script, dev protocols, configs, templates

<repo>/CLAUDE.md                 (Tier 3 — repo-specific, domain details only)
    ↓ contains: valid domains, version file, test commands, app-specific workflows
```

### How repos reference shared protocols

Each repo's `DEVELOPMENT_PROTOCOLS.md` points to:

```
../shared-resources/dev-protocols/
```

And adds only repo-specific details (domains, version file location, test commands).

### ThreatLocker hook

The canonical copy is `claude-hooks/threatlocker-guard.py`. It is referenced by `~/.claude/settings.json` as a PreToolUse hook for Bash and Write events. Individual repos should not have their own copies.

## Repos Using These Resources

| Repo | Has DEVELOPMENT_PROTOCOLS.md | Has CLAUDE.md |
|------|------------------------------|---------------|
| Knowledge-Manager | No (protocols in CLAUDE.md) | Yes (extensive) |
| Networker | Yes | Yes (extensive) |
| Product Manager | No | Yes |
| Accelo-agent | No | Yes |
| padding-outlook | Yes | No |
| availability-windows | Yes | No |
| contact-details-extractor | Yes | No |
| Proposal-reviewer | Yes | No |
| hr-manager | Yes (expected) | TBC |

Other repos in `~/GitHub/` (claude-code-templates, Funnel-Plan, etc.) inherit user-level CLAUDE.md and may adopt dev-protocols as needed.

## Security

**Never commit sensitive credentials.** The `.gitignore` excludes `credentials.txt`, `*.key`, `api-keys.txt`, and `.env`. Use template files in `templates/` as placeholders.

---

## Session Log

### 2026-02-18 — Cross-Repo Standards Consolidation

**Goal:** Establish shared standards across all align.me repos, eliminate duplication, and consolidate guardrails.

**Completed:**

1. **User-level CLAUDE.md created** (`~/.claude/CLAUDE.md`) — shared standards that all repos inherit automatically: ThreatLocker warning, permission request descriptions, locale (AEDT/Melbourne), company values, brand and writing standards, Knowledge Manager authority with Content Agent Request template, shared infrastructure references
2. **Repo renamed** from `common-runtime-resources` to `shared-resources` — GitHub remote updated via `gh repo rename`, local remote URL updated
3. **ThreatLocker hook consolidated** — canonical copy placed in `claude-hooks/threatlocker-guard.py`. Copies deleted from Knowledge-Manager, Networker, and Product Manager repos. User-level `~/.claude/settings.json` updated to point here
4. **Dev protocols created** — `dev-protocols/` folder with `BRANCH_PROTOCOLS.md`, `INSTRUCTIONS_FOR_CLAUDE.md`, and `BRANCH_GUIDE_TEMPLATE.md`. Synthesised from Networker (most comprehensive source) and boilerplate across 5 repos
5. **5 repos updated** — `DEVELOPMENT_PROTOCOLS.md` rewritten in padding-outlook, availability-windows, contact-details-extractor, Proposal-reviewer, and Networker. Replaced dead `../shared-dev-protocols/ai-guidelines/` references with `../shared-resources/dev-protocols/`. Deleted redundant `CLAUDE_PROTOCOLS.md` from all 5
6. **4 repo CLAUDE.md files trimmed** — removed duplicated ThreatLocker, locale, and KM authority sections from Knowledge-Manager, Networker, Product Manager, and Accelo-agent CLAUDE.md files (now inherited from user-level)
7. **Per-repo settings.json cleaned** — Knowledge-Manager hook removed (user-level covers it; kept PostToolUse for iteration-log publishing). Networker hook emptied
8. **This README rewritten** to reflect current repo structure and purpose

**Lesson learned:** When renaming a folder that contains the hook script referenced by `~/.claude/settings.json`, update the settings.json path **before** renaming. Python exit code 2 (file not found) collides with the hook "block" exit code, creating a deadlock where no tools can execute.

**Cross-reference:** Knowledge Manager iteration log, Session PL (2026-02-18)
