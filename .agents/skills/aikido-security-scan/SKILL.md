---
name: aikido-security-scan
description: Diagnose and fix failing Aikido Security Scan GitHub Actions workflows. Use when Aikido CI reports errors, new vulnerabilities, failed scan gates, timeouts, invalid Aikido configuration, missing AIKIDO_SECRET_KEY, or when Codex needs to use Aikido MCP to inspect and remediate security findings in this repository.
---

# Aikido Security Scan

## Workflow

Start by classifying the failure source before changing code.

1. Inspect `.github/workflows/aikido.yml` and the failing GitHub Actions run.
2. Run the helper when a run URL, run ID, or latest run is available:

```bash
python3 .agents/skills/aikido-security-scan/scripts/triage_aikido_action.py --repo AxelEriksson0/coding-template --latest
```

Use `--run-id <id>` for a specific run. Add `--json` when machine-readable output is useful. The helper uses `GITHUB_TOKEN` or `GH_TOKEN` if set; if GitHub refuses log downloads, fetch logs through GitHub MCP and rerun with `--log-file <path>`.

3. Classify the result:
   - `security-gate`: Aikido completed the scan and failed because `gate_passed=false` or new issues were found.
   - `auth`: missing, invalid, revoked, or inaccessible `AIKIDO_SECRET_KEY`.
   - `timeout`: scan did not complete within `timeout-seconds`.
   - `config`: invalid workflow inputs or all scan fail gates disabled.
   - `runtime`: action/runtime/network failures unrelated to a finding.

For `security-gate`, do not rely only on the action's final error wording. `AikidoSec/github-actions-workflow@v1.0.13` can report `dependency scan completed` even when the gate failed for another issue type. Prefer issue links, scan IDs, Aikido MCP issue data, and `new_*_issues_found` counters.

## Aikido MCP

This skill requires Aikido MCP for remediation. Use `tool_search` to expose Aikido tools. If tools such as `aikido_issues_list` and `aikido_full_scan` are not available, stop and report that Aikido MCP must be configured.

Expected Codex setup:

```bash
codex mcp add aikido \
  --env AIKIDO_API_KEY=YOUR_TOKEN \
  -- npx -y @aikidosec/mcp
```

Never write Aikido tokens to tracked files. The token must live in the MCP server environment.

Use Aikido MCP as follows:

- Call `aikido_issues_list` with `repo_name: coding-template` and relevant issue types: `open_source`, `sast`, `iac`, `leaked_secret`.
- Match MCP results to the failing Aikido issue link or dashboard issue ID from the GitHub log.
- Use the issue title, affected component/path, severity, and remediation guidance to choose the smallest fix.
- Run `aikido_full_scan` on changed or staged files before considering remediation complete.

If MCP returns multiple plausible issues or cannot expose the dashboard issue, ask the user to paste the Aikido issue details from the linked dashboard page.

## Fix Guidance

Prefer fixing the underlying issue over weakening CI.

- For open-source dependency issues, update the direct dependency or Yarn resolution that removes the vulnerable transitive version. Avoid broad dependency churn.
- For SAST issues, patch the vulnerable code path and add focused tests when behavior can regress.
- For IaC issues, fix the specific insecure setting and preserve deployment intent.
- For leaked secrets, remove the secret, rotate it outside the repo, and add or update secret-safe examples.
- For auth/config/runtime failures, fix workflow configuration only when the repository file is the cause. If the problem is an Aikido dashboard setting or GitHub secret, report the exact external change needed.

Do not change `minimum-severity`, disable `fail-on-dependency-scan`, or turn off the workflow unless the user explicitly accepts that policy change after seeing the security impact.

## Verification

After making a fix:

1. Run the relevant repository checks. For this repo, prefer:

```bash
yarn build
yarn lint
yarn ut
```

2. Run `aikido_full_scan` through MCP on the changed or staged files.
3. Rerun the failed GitHub Actions job or wait for the next workflow run.
4. Report the Aikido issue ID, scan ID, root cause, files changed, checks run, and whether the GitHub gate passed.
