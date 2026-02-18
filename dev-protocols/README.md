# Shared Dev Protocols

Universal development protocols for all align.me repos. These files define the shared workflow — branch creation, naming, session management, and branch guides.

## Files

| File | Purpose |
|------|---------|
| `BRANCH_PROTOCOLS.md` | Branch creation, naming, versioning, closure, hotfix workflow |
| `INSTRUCTIONS_FOR_CLAUDE.md` | Claude Code session guidelines — initialisation, file handling, documentation |
| `BRANCH_GUIDE_TEMPLATE.md` | Template for tracking work on a branch |

## What's shared vs. repo-specific

**Shared (in this folder):**
- Branch naming convention (`[version]-[type]-[domain]-[description]`)
- Branch creation/closure workflow
- Version calculation rules (patch/minor/major)
- Session initialisation steps
- File handling protocol
- Branch guide template structure

**Repo-specific (stays in each repo's CLAUDE.md or DEVELOPMENT_PROTOCOLS.md):**
- Valid domains for that repo
- Version file location (e.g. `version.py`, `README.md`)
- Test/build commands
- Application-specific workflows
- Code standards

## How repos reference these protocols

Each repo's `DEVELOPMENT_PROTOCOLS.md` or `CLAUDE.md` should reference:

```
../shared-resources/dev-protocols/
```

And add only repo-specific adaptations (domains, version file, test commands).
