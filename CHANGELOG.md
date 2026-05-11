# changelog

## 1.3.1

```text
removed stray temporary test file
cleaned shipped repo after verification
clarified python requirement and copied-output path for non-technical users
```

## 1.3.0

- added repo doctor command
- added validate-all command
- added compare fail-on-change mode for ci
- changed command adapter execution to avoid shell mode by default
- added explicit shell opt-in for trusted local adapters
- strengthened fixture validation with path and type checks
- added production readiness guide
- added security guide
- expanded unit tests from 4 to 8 checks
- updated ci workflow to run doctor and validate-all
- cleaned repo manifest wording

## 1.2.0

- removed generated reports from the shipped zip
- removed python cache files from the shipped zip
- rewrote article and docs to reduce repeated sentence shapes
- kept all commands and fixture examples in code blocks
- changed tests so local verification leaves no report files in the repo
- changed report lines to avoid grid-style formatting

## 1.1.0

- rewrote docs for beginner clarity
- added cleaned article draft
- kept captured-output mode as the safest default
- kept command mode for technical users
- kept tolerant jsonl session scanning

## 1.0.0

- initial replay runner
- fixture schema
- sample fixtures
- ci workflow
