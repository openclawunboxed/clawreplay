# openclaw integration guide

this repo never pretends every openclaw install has the same automation path.

openclaw setups differ by channel, gateway host, agent, auth, tools, skills, memory, and version.

captured output is the default path for that reason.

## method 1: captured output

send the fixture input to openclaw through your normal channel.

copy the agent reply into a text file under this folder:

```text
outputs/
```

run:

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/my_openclaw_reply.txt --label before-update
```

## method 2: command adapter

technical users wrap their own local command when they need a direct adapter.

the tool passes the fixture input to stdin and stores the same text in this environment variable:

```text
REPLAY_INPUT_TEXT
```

example:

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --command "your-command-here" --label before-update
```

replace the command with your adapter.

## method 3: session jsonl inspection

some openclaw setups write jsonl session logs under an agent directory.

scan a folder first:

```bash
python3 replay_lab.py scan-sessions ~/.openclaw/agents/main/sessions --out reports/session_scan.json
```

attach one session file to a run:

```bash
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/my_reply.txt --session-jsonl path/to/session.jsonl --label with-jsonl
```

the scanner looks for likely tool names, memory write-like events, token counts, and cost fields. it accepts varied jsonl shapes.

## after an openclaw update

run one fixture for each layer you depend on.

examples:

```text
channel fixture
memory fixture
skill fixture
cron fixture
customer or operator workflow fixture
```

score each fixture before the update.

score the same fixtures after the update.

compare the reports before trusting the workflow.

## avoid these as first tests

- real email sending
- real customer messages
- money movement
- production files
- private customer data
- browser login flows
- production credentials

start with fake data and a draft-only result.
