# advanced ci guide

this repo includes a github actions workflow.

it validates fixtures, runs demo checks, and runs unit tests.

## run locally

```bash
python3 replay_lab.py doctor
python3 replay_lab.py validate-all
python3 -m unittest tests.test_replay_lab
```

## fail when a fixture breaks

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/sample_after/fake_customer_refund.txt --label ci --fail-exit
```

## fail when before and after changed

```bash
python3 replay_lab.py compare runs/before.json runs/after.json --fail-on-change
```

## command adapter safety

command mode avoids shell execution by default.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --command "python3 examples/mock_agent.py fixtures/fake_customer_refund.json good" --label cmd-good
```

use `--shell` only for trusted local commands that need shell features.

## fixture design

use strict checks for behavior that must hold.

examples:

```text
a required field appears
a dangerous promise stays absent
a blocked tool stays unused
a memory write stays absent
a human review marker appears
```

avoid exact prose matching unless exact prose is the product.

## useful extensions

```text
add per-channel command adapters
export reports to an incident folder
run fixtures before dependency updates
run fixtures after skill edits
scan session jsonl during release tests
block deploys when fail-exit or fail-on-change returns a failing code
```
