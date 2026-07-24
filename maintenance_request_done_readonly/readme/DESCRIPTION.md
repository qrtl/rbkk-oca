This module makes completed maintenance requests read-only.

Once a request reaches a done stage, it can no longer be edited or reopened:
any attempt to change its fields (including moving it back out of the done
stage) is blocked. Only members of the *Equipment Manager* group keep full
access to completed requests.

The restriction is enforced on write, so every field is locked by default,
without having to enumerate them. Completing a request and its follow-up
(commenting, following, scheduling activities) keep working.

If some fields should stay editable after completion, an administrator can
select them in *Settings > Maintenance > Completed Requests*.
