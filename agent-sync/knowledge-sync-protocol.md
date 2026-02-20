# Knowledge Sync Protocol

How knowledge flows between agents, SharePoint, S3, and the Teams bots. Agreed between Knowledge Manager and Product Manager agents on 2026-02-20.

## Architecture — two-tier knowledge in the Teams Agent Gateway

The Teams Agent Gateway (`teams-agent-gateway` repo) serves both the Knowledge Manager and Product Manager bots in Microsoft Teams via AWS Lambda + Bedrock. Each bot has two tiers of knowledge:

| Tier | S3 location | Loaded when | Purpose | Size constraint |
|------|------------|-------------|---------|-----------------|
| **Core** | `agents/{agent-id}/knowledge/` | Every invocation (concatenated into system prompt) | Compact identity facts, key reference data | ~5-6 KB max |
| **RAG** | `rag/{site}/` | Per query (semantic search via Bedrock KB) | Full page corpus — all SP pages + PM knowledge files | No practical limit |

- **Core tier** is always available to the bot regardless of what the user asks. Keep it small and high-signal.
- **RAG tier** is retrieved per query — Bedrock searches the vector index and returns the most relevant chunks. Only content matching the bot's `rag_site_filter` is returned.

### Bedrock Knowledge Base

| Resource | Value |
|----------|-------|
| Knowledge Base ID | `IZ4LZID9FZ` |
| Data Source ID | `ETEPVEENU2` |
| Region | `ap-southeast-2` |
| Vector store | OpenSearch Serverless `teams-gateway-vectors`, index `knowledge-index` |
| Embedding model | Amazon Titan Embed v2 |
| Chunking strategy | 512-token semantic chunking |

## RAG source directories

The sync script (`teams-agent-gateway/scripts/sync_knowledge_to_s3.py`) reads `.md` files from these local directories and uploads them to the `rag/` prefix in S3:

| Source | Local path | S3 prefix | `site` metadata tag | Owner agent |
|--------|-----------|-----------|---------------------|-------------|
| Hub pages | `Knowledge-Manager/sp-extracted/hub` | `rag/hub/` | `hub` | Knowledge Manager |
| Onboarding pages | `Knowledge-Manager/sp-extracted/onboarding` | `rag/onboarding/` | `onboarding` | Knowledge Manager |
| Products pages | `Knowledge-Manager/sp-extracted/products` | `rag/products/` | `products` | Knowledge Manager |
| PM knowledge files | `Product Manager/knowledge` | `rag/product-manager/` | `product-manager` | Product Manager |

The script strips YAML frontmatter, generates `.metadata.json` sidecars with the `site` tag, and does incremental upload (skips unchanged files). After uploading, it triggers Bedrock re-ingestion (~2-5 min).

## Bot RAG filters

Each bot's manifest (`teams-agent-gateway/src/agents/{id}/manifest.json`) defines which `site` tags it can retrieve from:

| Bot | `rag_site_filter` | What it sees |
|-----|-------------------|-------------|
| Knowledge Manager | `["hub", "onboarding", "products"]` | All SP content |
| Product Manager | `["products", "product-manager", "hub", "onboarding"]` | All SP content + PM knowledge |

## Sync command

A single command refreshes the RAG corpus for both bots:

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
| Core tier file changes for either bot | That agent | Separate manual upload to `agents/{id}/knowledge/` on S3 (not covered by sync script) |
| PM needs an SP page changed | PM agent | Draft Content Agent Request for KM to process |

**Important:** The sync script does NOT manage core tier files. Core tier updates require a separate upload to `s3://alignme-agent-knowledge/agents/{agent-id}/knowledge/`.

## Content ownership

- **Knowledge Manager** owns: SP page publishing, Graph API operations, extraction to `sp-extracted/`, banners, validation, content standards enforcement, home page navigation, Content Agent pipeline
- **Product Manager** owns: Product strategy knowledge, Funnel Plan semantics, Funnel Camp/Academy deep knowledge, service portfolio analysis, pricing decisions
- **Handoff:** PM drafts Content Agent Requests when SP pages need changing. KM processes, publishes, and re-extracts
- **`sp-extracted/` files** are KM-managed caches of live SP pages. PM (and other agents) read them but never edit them directly

## Core tier files

These are manually managed and NOT covered by the sync script:

| Bot | S3 path | Current file(s) | Maintained by |
|-----|---------|-----------------|---------------|
| Knowledge Manager | `agents/knowledge-manager/knowledge/` | `sharepoint-knowledge.md` | KM agent |
| Product Manager | `agents/product-manager/knowledge/` | `core-summary.md` (pending confirmation) | PM agent |

Core tier files should be version-controlled in each agent's repo and uploaded to S3 when changed.

## Do NOT put detailed content in the core tier

The core tier is loaded into the system prompt on every invocation regardless of query. Putting large files there (e.g. all 37 PSD pages) would blow up token usage and cost. Detailed reference content belongs in the RAG tier, where it's retrieved only when relevant.
