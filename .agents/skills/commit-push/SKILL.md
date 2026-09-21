---
name: commit-push
description: Commit and push all current worktree changes when the user explicitly asks, splitting unrelated changes into multiple commits when useful. Use only when the user invokes /cp, asks to commit and push, or asks for this workflow.
---

# Commit Push

Use this skill only after an explicit user request such as `/cp`, "commit and push", or "make a commit and push it".

## Guardrails

- Never infer permission to commit or push from task completion.
- When this skill is invoked, the user wants all current worktree changes committed and pushed.
- Do not exclude files because they look unrelated. Split unrelated changes into separate commits when that makes the history clearer.
- Do not bypass failing checks unless the user explicitly accepts that risk.
- Do not run destructive git commands.

## Workflow

1. Inspect the worktree with `git status --short`.
2. Review changes with `git diff`; inspect untracked files before staging.
3. Decide whether the changes should be one commit or several commits. Use several commits when there are clearly independent groups, such as code changes, docs/notes, config, or skill updates.
4. Run the repo's required verification before committing unless the user explicitly told you to skip it. For this repo, use:
   - `pnpm build`
   - `pnpm format`
   - `pnpm lint`
5. For each commit group, stage the relevant files and commit with a concise imperative message.
6. Push the current branch after all commits are created.
7. Report the commit hash(es), branch, push result, and any checks that were skipped or failed.

## If Blocked

- If checks fail, fix the issue when it is in scope, then rerun the checks.
- If failures cannot be fixed safely, stop before committing and explain the blocker.
- If pushing requires credentials, network access, or upstream setup, ask for the needed approval or exact branch target.
