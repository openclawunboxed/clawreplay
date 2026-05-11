# quickstart

run the demo first. the sample never touches openclaw or real data.

## check the repo

mac or linux:

```bash
python3 replay_lab.py doctor
```

windows powershell:

```powershell
py replay_lab.py doctor
```

## safe sample

mac or linux:

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --label before
```

windows powershell:

```powershell
py replay_lab.py run fixtures/fake_customer_refund.json --label before
```

expected result:

```text
needs_review
```

## bad sample

mac or linux:

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/sample_after/fake_customer_refund.txt --label after
```

windows powershell:

```powershell
py replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/sample_after/fake_customer_refund.txt --label after
```

expected result:

```text
fail
```

## compare runs

copy the json paths printed by the two commands.

```bash
python3 replay_lab.py compare runs/before-file.json runs/after-file.json
```

## score your own openclaw reply

copy a fake openclaw reply into this file:

```text
outputs/my_openclaw_reply.txt
```

check the saved output:

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/my_openclaw_reply.txt --label my-output
```

## build your first fixture

copy this file:

```text
templates/fixture.template.json
```

place the copy here:

```text
fixtures/
```

rename it:

```text
my_first_workflow.json
```

edit the input path, required phrases, forbidden phrases, blocked tools, and review rule.

## beginner safety rule

start with a draft-only workflow.

avoid sending, deleting, refunds, purchases, production credentials, browser logins, and real customer data.
