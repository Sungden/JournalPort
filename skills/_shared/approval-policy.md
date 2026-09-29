# Approval policy

Only `SAFE_AUTOMATIC` and `CONTENT_PRESERVING_AUTOMATIC` actions may enter the automatic executor.
Stop and present `AUTHOR_APPROVAL_REQUIRED` actions. Never execute `FORBIDDEN_AUTOMATIC` actions.
Approval never authorizes a skill to invent an implementation for a semantic change; the current
core deliberately leaves semantic actions manual.
