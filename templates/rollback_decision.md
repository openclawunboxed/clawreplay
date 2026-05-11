# rollback decision sheet

rollback deserves attention when:

- a fixture that used to pass now fails
- an agent sends when the fixture requires a draft
- a channel no longer receives replies
- a workflow writes memory without approval
- secrets, auth, or tool credentials stop resolving
- a new risky tool appears in the session scan
- cost jumps and the reason is unclear

keep testing when:

- wording changed but the checks still pass
- status stayed the same
- a report says needs_review only because approval is required
- a release note explains the behavior change
- one fixture failed and the fix is isolated
