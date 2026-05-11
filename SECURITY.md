# security

clawreplay starts with fake data by design.

## safe defaults

```text
no live openclaw api call is required
no customer data is required
no credentials are required
no production inbox is required
no sending action is required
```

## command mode

command mode does not use shell execution by default.

use `--shell` only for trusted local adapters that need shell features.

## keep out of fixtures

```text
api keys
session tokens
customer private data
production passwords
browser cookies
real payment data
private health or legal records
```

## openclaw boundary

this repo checks behavior. it does not make an unsafe openclaw setup safe.

keep openclaw backups, doctor output, release notes, permission review, channel smoke tests, and human approvals in your process.
