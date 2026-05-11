# post update checklist

use this after changing openclaw, a model, a skill, memory, a channel, or gateway config.

1. confirm the gateway starts.
2. confirm the channel still sends and receives.
3. run the same replay fixtures from before the change.
4. compare before and after json results.
5. inspect every fail or needs_review report.
6. look for new tool calls.
7. look for memory writes.
8. check whether a draft-only workflow started sending or completing work.
9. check whether token or cost shape jumped.
10. choose keep, fix, or roll back.
