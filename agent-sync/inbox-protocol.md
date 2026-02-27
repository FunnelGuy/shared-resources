# Agent Inbox Protocol

How agents queue work for each other. Last updated 2026-02-21.

## Two queue mechanisms

| Target agent | Queue location | Mechanism |
|---|---|---|
| Knowledge Manager | SharePoint list ("Content Agent Requests" on Hub) | `queue_for_km.py` writes via Graph API; KM reads via `process_request.py --list-pending` |
| All other agents | `{agent-repo}/inbox/*.md` files | Any agent writes a request file; target agent checks inbox on session startup |

KM uses a SharePoint list because it already has a mature pipeline (Microsoft Form, Power Automate, process_request.py, Teams notifications). Other agents use file-based inboxes — lightweight and sufficient for agent-to-agent coordination.

## File-based inbox — format

Each request is a single `.md` file in the target agent's `inbox/` directory.

### Filename convention

```
{priority}-{YYYY-MM-DD}-{short-slug}.md
```

Examples:
- `urgent-2026-02-21-publish-our-team-page.md`
- `normal-2026-02-21-update-staff-directory.md`

Priority prefix ensures urgent items sort first alphabetically.

### Required frontmatter

```yaml
---
from: Head of AI Operations    # Source agent name
to: Product Manager            # Target agent name
date: 2026-02-21
priority: normal               # normal | urgent
type: knowledge-update         # See type list below
status: pending                # pending | in-progress | done | rejected
title: Update staff directory with contractor corrections
---
```

### Body

Free-form markdown describing what's needed. Be specific — the target agent should be able to act on this without further context.

### Request types

| Type | Use when |
|---|---|
| `knowledge-update` | Agent's CLAUDE.md or knowledge files need updating |
| `analysis` | Requesting data analysis or reporting |
| `review` | Asking agent to review content or decisions |
| `content-review` | KM routing a Content Agent Request for domain validation before publishing. Includes SP list item ID. Domain agent reviews content accuracy, edits the `sp-extracted/` markdown if needed, then queues a publish-ready request back to KM. |
| `content-draft` | Requesting content creation (non-SP — use KM queue for SP pages) |
| `configuration` | Infrastructure or config changes needed |
| `other` | Anything that doesn't fit above |

### Processing

When an agent starts a session:
1. Check `inbox/` for files with `status: pending`
2. Process them in priority order (urgent first, then by date)
3. Update the file's `status` field to `in-progress` while working
4. When complete, delete the file. The iteration log records what was done — no need to keep dead files.

### Example request file

```markdown
---
from: Head of AI Operations
to: Product Manager
date: 2026-02-21
priority: normal
type: knowledge-update
status: pending
title: Update staff directory with contractor corrections
---

The PM CLAUDE.md staff directory has been updated by Head of AI Operations:

- Moved Nick Steffens from "Resigned" to "Resigned, still contracting" (ID 31)
- Moved Callum Youla from "Current team" to "Resigned" (ID 65)
- Added Kate Watts (106), Aaheli Barman (97), Avelino Paginag (94), Asorthi Dimachki (89)

No further action needed — this is an FYI that the changes have been made directly.
```

## Queuing for KM (SharePoint list)

**Always submit immediately after drafting a request.** The JSON file is an input format for the script, not a deliverable. If you draft a request file but do not run `queue_for_km.py`, KM will never receive it.

Use the `queue_for_km.py` script from the Head of AI Operations repo:

```bash
# From any agent — submit via JSON file (avoids URL-in-args issues with ThreatLocker)
python "../head-of-ai-operations/scripts/queue_for_km.py" --from-file request.json

# Or with CLI args (if no URLs involved)
python "../head-of-ai-operations/scripts/queue_for_km.py" \
    --type Modify \
    --title "Update service pricing" \
    --site products \
    --description "Change Strategy Sprint from 4500 to 5200"

# List pending KM requests
python "../head-of-ai-operations/scripts/queue_for_km.py" --list-pending
```

## Who can queue for whom

Any agent can queue work for any other agent. Common patterns:

| From | To | Typical requests |
|---|---|---|
| Head of AI Ops | KM | Publish SP pages, content updates |
| Head of AI Ops | PM | Knowledge file updates, backlog items |
| Head of AI Ops | HR Manager | Recruitment/performance tasks |
| Head of AI Ops | Finance Manager | Revenue analysis requests |
| PM | KM | Products site page updates (via SP list) |
| KM | PM | "Products page X is stale — review and advise" |
| Any agent | Head of AI Ops | Cross-domain coordination, gap reports |
