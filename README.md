# clawreplay

replay one openclaw-style workflow before you trust a change.

this repo checks captured agent output against written fixture rules. use it before an openclaw update, model switch, skill edit, memory change, channel reconnect, cron change, or gateway move.

it does not call undocumented openclaw internals.

openclaw installs differ by channel, host, agent, auth, tools, skills, memory, and version. captured output stays the default path because every user has access to copy and paste. technical users get command adapters, tolerant jsonl scanning, ci checks, and fixture schemas.

## what you need

```text
python 3.10 or newer
no api keys
no openclaw internals
no live customer data
```

this works with any openclaw setup because the first path uses copied agent output, not a private integration.

## first run

open a terminal inside this folder.

```bash
cd clawreplay
```

if your folder uses a different downloaded name, use that folder instead.

check the repo.

```bash
python3 replay_lab.py doctor
```

windows powershell:

```powershell
py replay_lab.py doctor
```

run the safe sample.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --label before
```

windows powershell:

```powershell
py replay_lab.py run fixtures/fake_customer_refund.json --label before
```

expected result:

```text
status: needs_review
```

that is correct. customer replies need human review.

run the bad sample.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/sample_after/fake_customer_refund.txt --label after
```

expected result:

```text
status: fail
```

## use it with openclaw

pick one workflow that already works.

make a fake input for it.

send the fake input through your normal openclaw channel.

copy the answer into a file.

```text
outputs/my_openclaw_before.txt
```

score it.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/my_openclaw_before.txt --label before-update
```

change one layer, then send the same fake input again.

save the new answer.

```text
outputs/my_openclaw_after.txt
```

score the new answer.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/my_openclaw_after.txt --label after-update
```

compare the two result json files printed by the commands.

```bash
python3 replay_lab.py compare runs/before-update-file.json runs/after-update-file.json
```

replace the example names with your real run files.

## command mode

command mode passes the fixture input through stdin and this environment variable:

```text
REPLAY_INPUT_TEXT
```

safe default command mode does not run through a shell.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --command "python3 examples/mock_agent.py fixtures/fake_customer_refund.json good" --label cmd-good
```

use shell mode only for trusted local adapters that need shell features.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --command "your trusted shell command" --shell --label shell-adapter
```

## session jsonl scan

some setups write jsonl session logs. the scanner is tolerant because log shapes vary.

```bash
python3 replay_lab.py scan-sessions ~/.openclaw/agents/main/sessions --out reports/session_scan.json
```

attach one log file to a run.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/my_reply.txt --session-jsonl examples/sample_openclaw_session.jsonl --label with-session
```

## fixture checks

validate one fixture.

```bash
python3 replay_lab.py validate fixtures/fake_customer_refund.json
```

validate all bundled fixtures.

```bash
python3 replay_lab.py validate-all
```

## ci use

run local tests.

```bash
python3 -m unittest tests.test_replay_lab
```

fail when a comparison changes.

```bash
python3 replay_lab.py compare runs/before.json runs/after.json --fail-on-change
```

## included fixtures

```text
fake customer refund
telegram daily brief
cron status summary
memory dependency check
skill behavior check
```

begin with the fake customer refund fixture.

## safe first workflow

```text
telegram message comes in.
openclaw drafts a support reply.
the message stays unsent.
a human approves before action.
no permanent memory gets written.
```

that gives you a replay check without risking customers, money, files, or credentials.

## folder map

```text
fixtures/      replay rules
inputs/        fake task inputs
outputs/       sample and captured outputs
runs/          generated json results
reports/       generated markdown reports
examples/      mock agent and sample session log
scripts/       helper scripts
docs/          beginner and technical guides
templates/     checklists and fixture template
schema/        fixture schema
```

## production boundary

this is a replay and regression-check kit.

it is not a replacement for backups, openclaw doctor, release notes, permission review, channel smoke tests, or human approval.

start with fake data. keep real customer data, credentials, production files, payments, refunds, and browser logins out of first tests.
