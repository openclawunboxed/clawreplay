# repo manifest

this repo ships a standalone replay runner for openclaw-style workflows.

## core files

```text
replay_lab.py: cli runner, comparator, validator, doctor, and jsonl scanner
fixtures/: replay rules
inputs/: fake input messages
outputs/: sample outputs and user-captured outputs
reports/: generated markdown reports
runs/: generated json run files
templates/: checklists and starter fixture
docs/: beginner and technical guides
tests/: unit tests
.github/workflows/: ci smoke test
schema/: fixture schema
SECURITY.md: safe-use notes
PRODUCTION_READINESS.md: production boundary and workflow checklist
ARTICLE.md: public explainer article
```

## design choice

captured output comes first because openclaw setups vary by channel, host, auth, agent, skills, tools, memory, and version.

technical users attach command adapters and session jsonl scans when their setup supports them.
