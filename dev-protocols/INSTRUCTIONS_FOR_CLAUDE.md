# Instructions for Claude Code — Shared Dev Standards

Core development guidelines that apply when working in any align.me repo with active development (branch guides, version management, etc.).

## Session initialisation

At the start of every conversation:

1. **Check system prompt for current date** — use it for all timestamps
2. **Ask:** "Are you continuing work from a previous conversation, or starting something new?"
   - If **continuing**: request the branch guide and modified files from the previous session
   - If **new**: proceed to requirements gathering
3. **Classify work type:** bugfix, feature, refactor, admin, or hotfix
4. **Gather requirements** until success criteria are clear
5. **Calculate target version** and confirm with user
6. **Create branch guide** from the template before any code changes

## File handling

- **Never** work on files you haven't read in the current conversation
- **Never** assume file content or structure
- If errors reference unknown files, stop and request them
- Deliver one complete file at a time — never partial snippets
- Wait for user testing confirmation before proceeding to the next file

### Templates — central location, never copied

Word templates (.dotx) and other format templates live in one central location (currently Box, migrating to SharePoint). Never copy templates into repos, working folders, or anywhere else. The whole purpose of a template is that there is exactly one current version. Always reference templates by their central path.

### Word (.docx) files

The Read tool cannot open .docx files (binary format error). Use Python instead:

- **Read**: `from docx import Document; doc = Document(path)` — iterate `doc.paragraphs` for text, `doc.tables` for table data
- **Quick text extract** (no python-docx needed): use `zipfile` to open the .docx and parse `word/document.xml` with `xml.etree.ElementTree`
- **Create/modify**: use `python-docx` (`Document()`, add paragraphs/tables/styles, `doc.save(path)`)

`python-docx` is installed on this machine (`1.2.0`). Always prefer it over asking users to convert files to PDF or paste text.

## Branch guide maintenance

The branch guide is your **state management system**. Update it after every:
- File delivery
- Status change
- Issue discovered
- Design decision made
- Testing result
- Session break

Write branch guides as if you won't be the one finishing the work. Include enough detail for a new session to continue without redundant questions.

## Documentation updates

For every branch closure:

- [ ] Version file updated (e.g. `version.py`, `README.md`)
- [ ] Changelog entry added with user-facing changes and actual date
- [ ] README updated if user-facing functionality changed
- [ ] Architecture docs updated if structural changes made
- [ ] Code comments added for complex logic

## Error prevention

- Never create "release notes" instead of proper branch guides
- Never use generic branch/file names without version-type-domain-description format
- Never skip branch guide creation and status tracking
- Never proceed without reading the branch guide from a previous session
- Use **actual dates** from the system prompt — never placeholders

## Magic commands

- **"PROTOCOL CHECK"** — stop work, verify branch exists, verify branch guide exists, resume proper workflow
- **"Follow development protocol"** — initiate proper session start sequence
