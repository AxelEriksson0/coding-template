#!/usr/bin/env python3
"""Collect read-only remote disk usage diagnostics over SSH."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shlex
import subprocess
import sys
from pathlib import Path


REMOTE_SCRIPT = r"""#!/bin/sh
set +e
DIAGNOSTIC_TIMEOUT_SECONDS="__DIAGNOSTIC_TIMEOUT_SECONDS__"

section() {
  printf '\n## %s\n\n' "$1"
}

run() {
  printf '$ %s\n' "$*"
  if command -v timeout >/dev/null 2>&1; then
    timeout "$DIAGNOSTIC_TIMEOUT_SECONDS" "$@" 2>&1
  else
    "$@" 2>&1
  fi
  status=$?
  if [ "$status" -eq 124 ]; then
    printf '[timeout after %ss]\n' "$DIAGNOSTIC_TIMEOUT_SECONDS"
  elif [ "$status" -ne 0 ]; then
    printf '[exit %s]\n' "$status"
  fi
  printf '\n'
}

run_sh() {
  printf '$ %s\n' "$1"
  if command -v timeout >/dev/null 2>&1; then
    timeout "$DIAGNOSTIC_TIMEOUT_SECONDS" sh -c "$1" 2>&1
  else
    sh -c "$1" 2>&1
  fi
  status=$?
  if [ "$status" -eq 124 ]; then
    printf '[timeout after %ss]\n' "$DIAGNOSTIC_TIMEOUT_SECONDS"
  elif [ "$status" -ne 0 ]; then
    printf '[exit %s]\n' "$status"
  fi
  printf '\n'
}

section "Host"
run hostname
run date -u
run uptime
run uname -a

section "Filesystems"
run df -hT
run df -ih
if command -v lsblk >/dev/null 2>&1; then
  run lsblk -f
fi
if command -v findmnt >/dev/null 2>&1; then
  run findmnt -D
fi

section "Top-level directory usage"
for path in / /var /home /opt /srv /usr /tmp /var/log /var/lib /var/cache; do
  if [ -d "$path" ]; then
    run_sh "du -xhd1 $path 2>/dev/null | sort -h"
  fi
done

section "Large files over 500M"
run_sh "find / /var /home /opt /srv /tmp -xdev -type f -size +500M -exec ls -lh {} + 2>/dev/null | sort -k5 -h | tail -40"

section "Logs and journals"
if command -v journalctl >/dev/null 2>&1; then
  run journalctl --disk-usage
fi
if [ -d /var/log ]; then
  run_sh "du -sh /var/log/* 2>/dev/null | sort -h"
fi

section "Package caches"
if [ -d /var/cache/apt ] || [ -d /var/lib/apt/lists ]; then
  run_sh "du -sh /var/cache/apt /var/lib/apt/lists 2>/dev/null"
fi
if [ -d /var/cache/dnf ] || [ -d /var/cache/yum ]; then
  run_sh "du -sh /var/cache/dnf /var/cache/yum 2>/dev/null"
fi
if [ -d /var/cache/pacman ]; then
  run_sh "du -sh /var/cache/pacman 2>/dev/null"
fi

section "Container storage"
if command -v docker >/dev/null 2>&1; then
  run docker system df -v
fi
if command -v podman >/dev/null 2>&1; then
  run podman system df -v
fi
run_sh "du -sh /var/lib/docker /var/lib/containers /var/lib/containerd 2>/dev/null"

section "User caches and trash"
run_sh "du -sh /home/*/.cache /home/*/.local/share/Trash 2>/dev/null | sort -h"

section "Temporary directories"
run_sh "du -sh /tmp/* /var/tmp/* 2>/dev/null | sort -h | tail -40"
"""


def parse_env_file(env_file: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_file.exists():
        raise FileNotFoundError(f"missing env file: {env_file}")

    for line_number, raw_line in enumerate(env_file.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        if "=" not in line:
            raise ValueError(f"invalid .env line {line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"invalid .env line {line_number}: empty key")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def discover_repo_root(start: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return start.resolve()
    return Path(result.stdout.strip()).resolve()


def discover_env_file(repo_root: Path) -> Path:
    candidates: list[Path] = []
    root_env = repo_root / ".env"
    if root_env.is_file():
        candidates.append(root_env)

    packages_dir = repo_root / "packages"
    if packages_dir.is_dir():
        candidates.extend(
            sorted(
                path
                for path in packages_dir.glob("**/.env")
                if path.is_file()
            )
        )

    if not candidates:
        raise FileNotFoundError(
            f"missing .env; checked {root_env} and {packages_dir}/**/.env"
        )
    if len(candidates) > 1:
        formatted = "\n".join(f"  - {path}" for path in candidates)
        raise ValueError(
            "multiple .env files found; rerun with --env-file <path>:\n"
            f"{formatted}"
        )
    return candidates[0]


def build_ssh_command(env: dict[str, str]) -> list[str]:
    user = env.get("SERVER_USER", "").strip()
    host = env.get("SERVER_IP", "").strip()
    if not user or not host:
        missing = [
            name
            for name in ("SERVER_USER", "SERVER_IP")
            if not env.get(name, "").strip()
        ]
        raise ValueError(f"missing required .env value(s): {', '.join(missing)}")

    command = ["ssh"]

    ssh_config = env.get("SERVER_SSH_CONFIG", "").strip()
    command.extend(["-F", os.path.expanduser(ssh_config) if ssh_config else "/dev/null"])

    command.extend([
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ServerAliveInterval=15",
        "-o",
        "ServerAliveCountMax=2",
    ])

    port = env.get("SERVER_SSH_PORT", "").strip()
    if port:
        command.extend(["-p", port])

    key = env.get("SERVER_SSH_KEY", "").strip()
    if key:
        command.extend(["-i", os.path.expanduser(key)])

    command.extend([f"{user}@{host}", "sh -s"])
    return command


def command_timeout_seconds(env: dict[str, str]) -> int:
    raw_timeout = env.get("SERVER_DIAGNOSTIC_TIMEOUT", "").strip()
    if not raw_timeout:
        return 30
    try:
        timeout = int(raw_timeout)
    except ValueError as error:
        raise ValueError("SERVER_DIAGNOSTIC_TIMEOUT must be an integer") from error
    if timeout < 5 or timeout > 300:
        raise ValueError("SERVER_DIAGNOSTIC_TIMEOUT must be between 5 and 300 seconds")
    return timeout


def remote_script(command_timeout: int) -> str:
    return REMOTE_SCRIPT.replace(
        "__DIAGNOSTIC_TIMEOUT_SECONDS__",
        str(command_timeout),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run read-only disk usage diagnostics on SERVER_USER@SERVER_IP from repo .env."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root to search for .env. Defaults to git root or current directory.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Specific .env file to read. Use when multiple matching .env files exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the SSH command and remote script without connecting.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve() if args.repo_root else discover_repo_root(Path.cwd())
    try:
        env_file = args.env_file.resolve() if args.env_file else discover_env_file(repo_root)
        env = parse_env_file(env_file)
        ssh_command = build_ssh_command(env)
        timeout = command_timeout_seconds(env)
    except (FileNotFoundError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    target = ssh_command[-2]
    generated = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    print("# Remote Disk Usage Diagnostics")
    print()
    print(f"- Target: `{target}`")
    print(f"- Env file: `{env_file}`")
    print(f"- Generated: `{generated}`")
    print("- Mode: read-only diagnostics, no sudo, no cleanup")
    print(f"- Per-command timeout: `{timeout}s`")
    print()
    script = remote_script(timeout)

    if args.dry_run:
        printable = " ".join(shlex.quote(part) for part in ssh_command)
        print("## Dry run")
        print()
        print(f"SSH command: `{printable}`")
        print()
        print("Remote script:")
        print()
        print("```sh")
        print(script.rstrip())
        print("```")
        return 0

    try:
        result = subprocess.run(
            ssh_command,
            input=script,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("error: ssh executable not found", file=sys.stderr)
        return 127

    if result.returncode != 0:
        print()
        print(f"SSH command exited with status {result.returncode}.", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
