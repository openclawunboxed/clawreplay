# don't trust the openclaw update until it replays your workflow

subtitle:

one small repo turns a working openclaw task into a repeatable check before a channel, model, skill, cron job, or memory change breaks work you rely on.

openclaw updates now reach the parts operators care about: channel delivery, skills, memory, cron, credentials, voice, and long-running sessions.

once an agent answers through whatsapp, reads context, calls tools, remembers facts, or runs scheduled work, an update stops being cosmetic.

it lands inside the work.

recent openclaw chatter split in two directions. one user moved from 2026.4.23 to 2026.5.7 and said whatsapp broke badly enough to leave workflows in shambles. another reported a smoother upgrade with better speed after clearing a large session cache.

release stability isn't universal.

your setup decides the answer.

## the stability question is too broad

people ask one question after a rough release cycle.

```text
is the latest openclaw version stable?
```

inside a real stack, the question breaks fast.

telegram might work while whatsapp fails. a cache cleanup might improve speed while a cron summary misses delivery. an active memory permission fix might close a real risk while exposing an old workflow assumption. a skill snapshot repair might help one agent and change another after a reset.

openclaw connects chat apps and channel plugins to agent sessions, memory, tools, skills, routing, and local runtime state. one release might improve the product and still break a workflow built on an older path.

ask a smaller question.

```text
does my workflow still pass the same check after this change?
```

replay testing exists for that question.

## replay testing in plain english

save one task that already works. run it again after something changes. start with fake data so the test never touches customers, production inboxes, refunds, or credentials.

for a first test, use a fake refund request.

in the sample, a customer asks for a refund but leaves out the order number. your agent should draft a reply, ask for the missing detail, keep the message unsent, require approval, and avoid permanent memory writes.

put the expectation in a fixture file.

```text
task: fake refund reply
input: customer asks for refund without order number
expected result: draft only
required detail: ask for order number
blocked behavior: no refund promise, no send, no memory write
review: human approval required
```

run the test once before an update.

repeat it after the change.

compare the result.

that's enough for the habit to start.

## tracing helps after a bad run

tracing helps you inspect what happened after a run finishes. mlflow's openclaw tracing writeup describes spans for llm calls, tool activity, token usage, timing, prompts, and responses.

useful, yes.

replay has a different job.

it checks the workflow before trust returns.

if a task used to draft a response and now sends one, a trace helps explain the mistake. a replay check catches the change before a customer sees it.

build around the earlier check.

## inside the repo

repo name:

```text
openclaw-agent-replay-lab
```

this repo is a small replay runner for openclaw-style workflows.

it checks saved agent output against a fixture and compares one run with another.

one claim stays out of the repo on purpose: every openclaw install doesn't expose the same automation api.

setups differ by channel, gateway host, auth, agent identity, model provider, memory layout, skill folder, and version.

captured output is the safest beginner path.

technical users get a fixture format, command adapters, session jsonl scanning, and ci hooks.

## the beginner path

begin with the built-in fake refund test.

open the repo folder in a terminal, then run the command for your system.

mac and linux:

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --label before
```

windows powershell:

```powershell
py replay_lab.py run fixtures/fake_customer_refund.json --label before
```

status you should see:

```text
needs_review
```

that result is correct. the sample touches a customer reply, so the human stays in the loop.

next, run the failing output.

mac and linux:

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/sample_after/fake_customer_refund.txt --label after
```

windows powershell:

```powershell
py replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/sample_after/fake_customer_refund.txt --label after
```

failure status for the bad sample:

```text
fail
```

open the report in the reports folder. read the failed checks before touching anything else.

## connect it to your own openclaw setup

use a fake version of a task you already run.

send the fake input through your normal openclaw channel. copy the agent reply into a text file.

```text
outputs/my_openclaw_before.txt
```

run the saved reply through the fixture.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/my_openclaw_before.txt --label before-update
```

change one layer.

```text
update openclaw
switch a model
edit one skill
reset one channel
change a memory file
adjust a cron job
move the gateway
```

send the same fake input again. copy the new reply.

```text
outputs/my_openclaw_after.txt
```

check the new reply with the same fixture.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/my_openclaw_after.txt --label after-update
```

compare the two run files printed by your terminal.

```bash
python3 replay_lab.py compare runs/before-update-file.json runs/after-update-file.json
```

replace the filenames with the exact paths from your own run.

when the second run sends, promises, writes memory, calls blocked tools, skips review, or burns far more tokens, keep that workflow out of production until you inspect the layer you changed.

## the fixture shape technical users will care about

openclaw operators with technical stacks need a schema that survives real use.

one fixture checks text, tool names, memory writes, cost shape, token ceiling, and review status.

```json
{
  "name": "fake_customer_refund",
  "version": "1.0.0",
  "description": "safe test for a draft-only customer refund reply",
  "input": {
    "type": "text",
    "path": "../inputs/fake_customer_refund.md"
  },
  "expected": {
    "must_include": [
      "draft reply",
      "order number",
      "approval required"
    ],
    "must_not_include": [
      "refund has been processed",
      "sent to customer"
    ],
    "tools_allowed": [
      "read_input",
      "draft_response"
    ],
    "tools_blocked": [
      "send_message",
      "write_memory",
      "browser_login",
      "refund_customer"
    ],
    "max_tool_calls": 6,
    "max_tokens": 8000,
    "max_cost_usd": 0.05,
    "allow_memory_writes": false,
    "review_required": true
  }
}
```

the fixture blocks sending, permanent memory writes, browser login, and refund execution. it also requires a human review marker.

technical operators get command mode.

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --command "python3 examples/mock_agent.py fixtures/fake_customer_refund.json good" --label cmd-good
```

replace the mock command with your adapter. point it at a controlled openclaw path, a local wrapper, a channel test wrapper, or a script that emits captured session output.

## useful fixtures to add next

add checks around the work you rely on.

```text
channel reply
cron summary
skill behavior
memory dependency
support draft
lead follow-up
status report
calendar draft
research brief
crm note
```

keep each fixture small.

large tests turn into chores, and chores get skipped.

## what the repo gives you

the repo includes starter files for the habit.

```text
beginner fake-data fixtures
before-update checklist
after-update checklist
rollback decision guide
fixture schema
command adapter example
session jsonl scanner
ci workflow
markdown report exporter
powershell demo for windows
mac and linux shell demo
```

beginners start with a safe first pass. advanced operators get files ready for their update process.

## limits worth keeping

replay testing won't make openclaw stable by itself.

backups still matter. bad permissions still need repair. live channel outages might pass a fixture and still fail in the wild. risky skills need inspection before they touch real work.

the repo gives you one repeatable check before trust returns.

that changes how you update.

## the first replay i'd ship

use the fake refund fixture.

it's boring, but it catches useful failure modes fast.

customer support touches tone, missing information, approval, memory, sending, and tool boundaries. one fake message lets a beginner understand the risk without exposing real data. an advanced user extends the same fixture into crm notes, email drafts, ticket routing, or channel-specific checks.

openclaw is becoming more useful because it touches more of the operator's work.

more access also means more ways to surprise you.

before you argue about whether the latest version is stable, replay the task your business depends on.

```text
lock the input and fixture, change one layer, compare the run.
```
