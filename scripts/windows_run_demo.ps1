$ErrorActionPreference = "Stop"

py replay_lab.py doctor
py replay_lab.py validate-all
py replay_lab.py run fixtures/fake_customer_refund.json --label demo-before
py replay_lab.py run fixtures/fake_customer_refund.json --actual outputs/sample_after/fake_customer_refund.txt --label demo-after

Write-Host "demo complete. open the newest files in reports/."
