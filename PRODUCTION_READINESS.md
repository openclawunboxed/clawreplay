# production readiness

this repo is production-ready as a replay and regression-check kit.

it is not a live openclaw automation runtime.

## verified production boundary

```text
works with copied openclaw output from any channel
works without private openclaw internals
uses fake data for first tests
uses command adapters only when the operator supplies one
```

## before using on real workflows

```text
run doctor
validate all fixtures
run the safe sample
run the bad sample
compare before and after outputs
use fake data first
keep generated reports out of git
keep captured private outputs out of git
```

## minimum production habit

```text
capture a fake version of one workflow
score it before a change
score it after the change
compare the two runs
hold the workflow if status, blocked actions, memory writes, or cost shape changed
```

## best first production-adjacent checks

```text
support draft
telegram brief
cron summary
memory dependency
skill behavior
```

## what still needs your judgment

```text
live channel outages
bad openclaw permissions
unsafe third-party skills
production credentials
browser login flows
customer-facing sends
payments, refunds, and account changes
```
