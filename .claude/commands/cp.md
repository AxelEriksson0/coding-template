Stage all changes (including untracked files), then commit with a short but descriptive message that reflects the actual changes, and push to the remote branch.

Follow the Git Safety Protocol from your system instructions when committing (e.g. never skip hooks, never force push to main).

## Handling auto-fixes from pre-commit hooks

After the commit completes, run `git status` to check for any unstaged changes left behind by the pre-commit hooks (e.g. files reformatted by `pnpm format`). If there are any, stage and commit them immediately with the message `chore: apply auto-fixes from pre-commit hooks` before pushing.
