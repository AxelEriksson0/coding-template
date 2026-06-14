---
name: ssh-disk-usage-report
description: SSH into a remote server using SERVER_USER and SERVER_IP from a repository .env file, run read-only disk usage diagnostics, and produce a cleanup report. Use when the user asks to investigate server disk space, find what is using storage, debug full disks, or recommend safe cleanup candidates without executing cleanup.
---

# SSH Disk Usage Report

## Workflow

Use `scripts/remote_disk_report.py` from the skill directory. Run it from the local repository, or pass `--repo-root <path>`.

```bash
python3 .agents/skills/ssh-disk-usage-report/scripts/remote_disk_report.py
```

The script searches for `.env` in this order:

1. `<repo-root>/.env`
2. `<repo-root>/packages/**/.env`

If multiple `.env` files are found, rerun with `--env-file <path>` rather than guessing.

The script reads these keys from the selected `.env`:

- Required: `SERVER_USER`, `SERVER_IP`
- Optional: `SERVER_SSH_PORT`, `SERVER_SSH_KEY`, `SERVER_SSH_CONFIG`, `SERVER_DIAGNOSTIC_TIMEOUT`

By default, the helper passes `-F /dev/null` to SSH so local/system SSH config cannot break direct diagnostics inside Codex sandboxing. Set `SERVER_SSH_CONFIG` to a specific config path only when this server needs custom SSH behavior such as `ProxyJump`.

Remote commands stream output as they run and are bounded by `SERVER_DIAGNOSTIC_TIMEOUT` seconds per command. The default is 30 seconds.

## Guardrails

- Run diagnostics only. Do not delete, truncate, vacuum, prune, rotate, or restart anything on the server.
- Do not use `sudo`. If access is denied, include that limitation in the report and suggest specific sudo read-only commands the user could run manually.
- Use SSH batch mode. If authentication, host key verification, or connectivity fails, report the blocker and stop.
- Treat container, package-cache, journal, and log cleanup as recommendations only. Include risk notes before suggesting commands.

## Report Format

After the script finishes, summarize the output in Markdown:

1. **Disk Summary**: filesystems near capacity, inode pressure, and mounted volumes that matter.
2. **Largest Usage**: biggest directories and files found, grouped by path.
3. **Likely Cleanup Candidates**: low-risk items first, such as package caches, old logs, temp files, unused container data, or obvious stale artifacts.
4. **Commands To Consider**: commands the user may run manually. Mark destructive or service-affecting commands clearly.
5. **Unknowns / Permission Gaps**: directories that could not be inspected without elevated privileges.

Keep the report specific to the observed output. Do not recommend cleanup for tools that are not installed or paths that were not present.
