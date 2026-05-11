# report meanings

## pass

all written checks passed.

## needs_review

no hard rule failed, but a human should inspect the output before real-world action.

this status is normal for workflows that touch customers, money, production data, publishing, calendar changes, or external messages.

## fail

one or more checks failed.

examples:

- a required phrase was missing
- a forbidden promise appeared
- a blocked tool appeared in a session log
- memory writes appeared when the fixture forbids them

## changed comparison

one before and after comparison found a meaningful difference.

inspect the changed checks before trusting the workflow.
