# Shared Resources

You are working in the **Shared Resources** repo — the centralised repository holding shared development protocols, ThreatLocker guardrails, inter-agent coordination protocols, and credential templates used across all align.me GitHub repos.

This repo does not have its own agent identity — it is infrastructure that all agents reference. Changes here affect the entire agent workforce.

## Session protocol

### On session start
1. Read `iteration-log.md` — understand prior context, recent decisions, and open questions.
2. Mention any pending items to the operator.

### Before session close
1. Update `iteration-log.md` with a session entry covering: what was done, decisions made, and open questions.
2. Include a **Backlog impact** section in the iteration log entry listing all backlog item completions, status changes, and new items discovered. Use explicit item numbers and status transitions (e.g. `1.3 Not started → Done`, `NEW: Description`). Head of AI Operations will update the master backlog from this section.

## Inter-agent coordination

This repo is the canonical source for inter-agent coordination standards. Key files:

- `agent-sync/knowledge-sync-protocol.md` — Teams Agent Gateway two-tier knowledge architecture.
- `agent-sync/inbox-protocol.md` — how agents queue work for each other via `inbox/` directories.
- `dev-protocols/` — shared development standards referenced by individual agent repos.
- `claude-hooks/threatlocker-guard.py` — canonical ThreatLocker hook, referenced by `~/.claude/settings.json`.

### Related agents (all repos reference this one)

- **Head of AI Operations** (`../head-of-ai-operations/`) — cross-domain coordination, agent standards.
- **Knowledge Manager** (`../Knowledge-Manager/`) — SharePoint page CRUD.
- **Product Manager** (`../Product Manager/`) — product strategy.
- **Finance Manager** (`../finance-manager/`) — revenue and billing analysis (Accelo + Xero).
- **HR Manager** (`../hr-manager/`) — recruitment and performance.
- **Teams Agent Gateway** (`../teams-agent-gateway/`) — shared Lambda for Teams bots.
- **Networker** (`../Networker/`) — LinkedIn connection management.
- **alignme-aws-admin** (`../alignme-aws-admin/`) — AWS environment ops.
