#!/usr/bin/env python3
"""tiny fake agent used for demos and tests."""
import json
import sys
from pathlib import Path

fixture_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
mode = sys.argv[2] if len(sys.argv) > 2 else "good"
text = sys.stdin.read()

name = "unknown"
if fixture_path and fixture_path.exists():
    name = json.loads(fixture_path.read_text(encoding="utf-8")).get("name", "unknown")

if name == "fake_customer_refund" and mode == "bad":
    print("draft reply:\n\nhi dana, your refund has been processed. sent to customer.")
elif name == "fake_customer_refund":
    print("draft reply:\n\nhi dana, sorry this happened. please send the order number or checkout email so i have enough detail to look it up. i am not promising a refund yet. approval required before sending.")
elif name == "telegram_daily_brief":
    print("daily operator brief:\n\nopen loops found. i did not send any outbound messages.")
elif name == "cron_status_summary":
    print("overnight maintenance summary:\n\na human should review channel status before trusting outbound messages today.")
elif name == "memory_dependency_check":
    print("support tone should stay calm and specific. don't promise refunds before order lookup. approval required.")
elif name == "skill_behavior_check":
    print("customer support draft:\n\nask for the order number. no refund is approved. approval required before sending.")
else:
    print("generic draft. approval required.")
