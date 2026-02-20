# Knowledge Sync Protocol

How knowledge flows between agents, SharePoint, S3, and the Teams bots. Last updated 2026-02-20.

## Architecture — two-tier knowledge in the Teams Agent Gateway

The Teams Agent Gateway (`teams-agent-gateway` repo) serves multiple bots in Microsoft Teams via AWS Lambda + Bedrock. Each bot has two tiers of knowledge:

| Tier | S3 location | Loaded when | Purpose | Size constraint |
|------|------------|-------------|---------|-----------------|
| **Core** | `agents/{agent-id}/knowledge/` | Every invocation (concatenated into system prompt) | Compact identity facts, key reference data | ~5-6 KB max |
| **RAG** | `rag/{site}/` | Per query (semantic search via Bedrock KB) | Full page corpus — all SP pages + agent knowledge files | No practical limit |

- **Core tier** is always available to the bot regardless of what the user asks. Keep it small and high-signal.
- **RAG tier** is retrieved per query — Bedrock searches the vector index and returns the most relevant chunks. Only content matching the bot's `rag_site_filter` is returned.

### Bedrock Knowledge Base

| Resource | Value |
|----------|-------|
| Knowledge Base ID | `IZ4LZID9FZ` |
| Data Source ID | `ETEPVEENU2` |
| Region | `ap-southeast-2` |
| Vector store | S3 Vectors `teams-gateway-vectors`, index `knowledge-index` |
| Embedding model | Amazon Titan Embed v2 |
| Chunking strategy | 512-token semantic chunking |

## Registered bots

| Bot | Agent ID | Bot App ID | Status |
|-----|----------|-----------|--------|
| Knowledge Manager | `knowledge-manager` | `fe9f9714-6d95-4be3-ac16-dfbc88998b5a` | Live |
| Product Manager | `product-manager` | `206d5fc4-ab6f-4dfe-8940-afacf9b26df6` | Live |
| HR Manager | `hr-manager` | *pending registration* | Config ready, awaiting Azure Bot registration |
| Accelo Agent | `accelo-agent` | *pending registration* | Config ready, awaiting Azure Bot registration |

### Adding a new bot

1. **Hugh registers the bot** in Azure Portal → Bot Services → Create Azure Bot. VITG approves the registration in the tenant.
2. **Store credentials** in Secrets Manager: `teams-bot/{agent-id}/credentials` with `microsoft_app_id`, `microsoft_app_password`, `microsoft_app_tenant_id`.
3. **Create agent directory** in `src/agents/{agent-id}/` with `manifest.json`, `system-prompt.md`, and `knowledge/` directory.
4. **Update `manifest.json`** with the real `bot_app_id` from Azure.
5. **Upload core knowledge** to `s3://alignme-agent-knowledge/agents/{agent-id}/knowledge/`.
6. **Add RAG sources** to `scripts/sync_knowledge_to_s3.py` if the agent has local knowledge files to index.
7. **Deploy** the Lambda (the agent registry auto-discovers new agents on cold start).

## RAG source directories

The sync script (`teams-agent-gateway/scripts/sync_knowledge_to_s3.py`) reads `.md` files from these local directories and uploads them to the `rag/` prefix in S3:

| Source | Local path | S3 prefix | `site` metadata tag | Owner agent |
|--------|-----------|-----------|---------------------|-------------|
| Hub pages | `Knowledge-Manager/sp-extracted/hub` | `rag/hub/` | `hub` | Knowledge Manager |
| Onboarding pages | `Knowledge-Manager/sp-extracted/onboarding` | `rag/onboarding/` | `onboarding` | Knowledge Manager |
| Products pages | `Knowledge-Manager/sp-extracted/products` | `rag/products/` | `products` | Knowledge Manager |
| PM knowledge files | `Product Manager/knowledge` | `rag/product-manager/` | `product-manager` | Product Manager |
| HR recruitment files | `hr-manager/knowledge-base/recruitment` | `rag/hr-manager/` | `hr-manager` | HR Manager |
| HR performance files | `hr-manager/knowledge-base/performance` | `rag/hr-manager/` | `hr-manager` | HR Manager |

The script strips YAML frontmatter, generates `.metadata.json` sidecars with the `site` tag, and does incremental upload (skips unchanged files). After uploading, it triggers Bedrock re-ingestion (~2-5 min).

**Note:** Accelo Agent has no local RAG files — its domain knowledge is procedural (CLAUDE.md + analysis scripts). It relies on core tier knowledge plus Products SP pages for cross-referencing services.

## Bot RAG filters

Each bot's manifest (`teams-agent-gateway/src/agents/{id}/manifest.json`) defines which `site` tags it can retrieve from:

| Bot | `rag_site_filter` | What it sees |
|-----|-------------------|-------------|
| Knowledge Manager | `["hub", "onboarding", "products"]` | All SP content |
| Product Manager | `["products", "product-manager", "hub", "onboarding"]` | All SP content + PM knowledge |
| HR Manager | `["hr-manager", "hub", "onboarding"]` | HR knowledge + Hub + Onboarding SP pages |
| Accelo Agent | `["accelo-agent", "products"]` | Products SP pages (for service cross-reference) |

## Sync command

A single command refreshes the RAG corpus for all bots:

```bash
python "c:/Users/HughMacfarlane/GitHub/teams-agent-gateway/scripts/sync_knowledge_to_s3.py" --profile Admin-351596828163
```

Options: `--dry-run` (preview without uploading), `--skip-ingestion` (upload only, don't trigger Bedrock re-ingestion).

The script needs KB and data source IDs to trigger ingestion. Pass via CLI args (`--knowledge-base-id IZ4LZID9FZ --data-source-id ETEPVEENU2`) or set environment variables `KNOWLEDGE_BASE_ID` and `DATA_SOURCE_ID`.

## When to sync

| Trigger | Who flags | Action for Hugh |
|---------|----------|-----------------|
| KM publishes or re-extracts SP pages | KM agent | Run sync script |
| PM updates `knowledge/*.md` files | PM agent | Run sync script |
| HR Manager updates `knowledge-base/*.md` files | HR Manager agent | Run sync script |
| Core tier file changes for any bot | That agent | Separate manual upload to `agents/{id}/knowledge/` on S3 (not covered by sync script) |
| Any agent needs an SP page changed | That agent | Draft Content Agent Request for KM to process |

**Important:** The sync script does NOT manage core tier files. Core tier updates require a separate upload to `s3://alignme-agent-knowledge/agents/{agent-id}/knowledge/`.

## Content ownership

- **Knowledge Manager** owns: SP page publishing, Graph API operations, extraction to `sp-extracted/`, banners, validation, content standards enforcement, home page navigation, Content Agent pipeline
- **Product Manager** owns: Product strategy knowledge, Funnel Plan semantics, Funnel Camp/Academy deep knowledge, service portfolio analysis, pricing decisions
- **HR Manager** owns: Recruitment framework (10 modules), performance management workflows, HR templates and standards
- **Accelo Agent** owns: Revenue analysis methodology, Accelo data model knowledge, billing and retainer portfolio analysis
- **Handoff:** All agents draft Content Agent Requests when SP pages need changing. KM processes, publishes, and re-extracts
- **`sp-extracted/` files** are KM-managed caches of live SP pages. All other agents read them but never edit them directly

## Core tier files

These are manually managed and NOT covered by the sync script:

| Bot | S3 path | Current file(s) | Maintained by |
|-----|---------|-----------------|---------------|
| Knowledge Manager | `agents/knowledge-manager/knowledge/` | `sharepoint-knowledge.md` | KM agent |
| Product Manager | `agents/product-manager/knowledge/` | `core-summary.md` | PM agent |
| HR Manager | `agents/hr-manager/knowledge/` | `hr-core-summary.md` | HR Manager agent |
| Accelo Agent | `agents/accelo-agent/knowledge/` | `accelo-core-summary.md` | Accelo Agent |

Core tier files should be version-controlled in each agent's repo and uploaded to S3 when changed.

## Do NOT put detailed content in the core tier

The core tier is loaded into the system prompt on every invocation regardless of query. Putting large files there (e.g. all 37 PSD pages or all 10 HR modules) would blow up token usage and cost. Detailed reference content belongs in the RAG tier, where it's retrieved only when relevant.

## Head of AI Operations

The **Head of AI Operations** (`head-of-ai-operations/`) is a Claude Code agent that manages align.me's AI agent workforce. It acts as Hugh's single entry point for all agent work — reading specialist CLAUDE.md and knowledge files on demand, running scripts from any repo, and connecting to all MCP servers (Confluence, JIRA, Accelo, Box). It does NOT have a Teams bot — it is a Claude Code interface only.

All other agents have a dotted line to Head of AI Operations for build, operations, coordination, and standards. It does not own any content or knowledge — it reads from source repos and routes work to the appropriate specialist context.

## Inter-agent work queue

Agents queue work for each other instead of requiring Hugh to copy-paste prompts between sessions. Full protocol: `inbox-protocol.md` (in this directory).

### Two mechanisms

| Target | Queue | Writer | Reader |
|---|---|---|---|
| Knowledge Manager | SharePoint list ("Content Agent Requests" on Hub) | `head-of-ai-operations/scripts/queue_for_km.py` | `Knowledge-Manager/scripts/process_request.py --list-pending` |
| All other agents | `{agent-repo}/inbox/*.md` files | Any agent writes directly | Target agent checks inbox on session start |

### How it works

1. **Agent A** finishes work that requires Agent B's action.
2. **If Agent B is KM** (SP page change): Agent A runs `queue_for_km.py` which writes to the SharePoint list via Graph API. This integrates with KM's existing pipeline (Microsoft Form, Power Automate, process_request.py).
3. **If Agent B is any other agent**: Agent A writes a structured `.md` file to `{Agent B's repo}/inbox/`.
4. **Next time Hugh opens Agent B**, it checks its queue on startup and mentions pending items.
5. **Agent B processes the request**, updates its status, adds a resolution note, and moves it to `inbox/processed/`.

### Trigger

The trigger for processing queued work is currently manual — Hugh opens the agent. Future enhancements (email-to-agent pipeline, scheduled automation) will add more autonomous triggering.
