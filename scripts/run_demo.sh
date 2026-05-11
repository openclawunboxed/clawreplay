#!/usr/bin/env bash
set -euo pipefail

python3 replay_lab.py doctor
python3 replay_lab.py validate-all
python3 replay_lab.py run fixtures/fake_customer_refund.json --label demo-before
python3 replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/sample_after/fake_customer_refund.txt --label demo-after

echo "demo complete. open the newest files in reports/."
