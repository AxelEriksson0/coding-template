#!/usr/bin/env python3
"""Summarize Aikido Security Scan GitHub Actions failures."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from io import BytesIO
from typing import Any


DEFAULT_REPO = "AxelEriksson0/coding-template"
DEFAULT_WORKFLOW = "aikido.yml"


@dataclass
class Triage:
    repo: str
    run_id: int
    run_url: str
    conclusion: str | None
    job_id: int | None
    failed_step: str | None
    classification: str
    scan_ids: list[str]
    issue_ids: list[str]
    issue_links: list[str]
    errors: list[str]
    warnings: list[str]
    notes: list[str]


def github_json(path_or_url: str) -> Any:
    if path_or_url.startswith("https://"):
        url = path_or_url
    else:
        url = f"https://api.github.com{path_or_url}"
    request = urllib.request.Request(url, headers=github_headers("application/vnd.github+json"))
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def github_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers=github_headers("application/vnd.github+json"))
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def github_headers(accept: str) -> dict[str, str]:
    headers = {"Accept": accept}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def latest_run(repo: str, workflow: str) -> dict[str, Any]:
    encoded_workflow = urllib.parse.quote(workflow, safe="")
    payload = github_json(f"/repos/{repo}/actions/workflows/{encoded_workflow}/runs?per_page=1")
    runs = payload.get("workflow_runs") or []
    if not runs:
        raise SystemExit(f"No workflow runs found for {repo} workflow {workflow}")
    return runs[0]


def run_by_id(repo: str, run_id: int) -> dict[str, Any]:
    return github_json(f"/repos/{repo}/actions/runs/{run_id}")


def run_jobs(repo: str, run_id: int) -> list[dict[str, Any]]:
    payload = github_json(f"/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100")
    return payload.get("jobs") or []


def job_logs(repo: str, job_id: int) -> str:
    url = f"https://api.github.com/repos/{repo}/actions/jobs/{job_id}/logs"
    data = github_bytes(url)
    if zipfile.is_zipfile(BytesIO(data)):
        with zipfile.ZipFile(BytesIO(data)) as archive:
            return "\n".join(
                archive.read(name).decode("utf-8", errors="replace")
                for name in archive.namelist()
                if not name.endswith("/")
            )
    return data.decode("utf-8", errors="replace")


def clean_log_line(line: str) -> str:
    line = line.lstrip("\ufeff")
    line = re.sub(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+Z\s+", "", line)
    line = line.replace("##[error]", "ERROR: ")
    line = line.replace("##[warning]", "WARNING: ")
    return line.strip()


def classify(logs: str, errors: list[str]) -> str:
    joined = "\n".join(errors) + "\n" + logs
    lower = joined.lower()
    if "new issue detected" in lower or "new issue(s) detected" in lower or "gate_passed" in lower:
        return "security-gate"
    if "secret key not set" in lower or "api key" in lower or "401" in lower or "revoked" in lower:
        return "auth"
    if "time out" in lower or "timeout" in lower:
        return "timeout"
    if "invalid property value" in lower or "you must enable at least one of the scans" in lower:
        return "config"
    return "runtime" if errors else "unknown"


def parse_logs(logs: str) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    lines = [clean_log_line(line) for line in logs.splitlines()]
    errors = [line.removeprefix("ERROR: ").strip() for line in lines if line.startswith("ERROR: ")]
    warnings = [line.removeprefix("WARNING: ").strip() for line in lines if line.startswith("WARNING: ")]
    scan_ids = sorted(set(re.findall(r'scan with id: "?(\d+)"?', logs)))
    issue_links = sorted(set(re.findall(r"https://app\.aikido\.dev/[^\s\"']+", logs)))
    issue_ids = sorted(set(re.findall(r"sidebarIssue=(\d+)", "\n".join(issue_links))))
    return errors, warnings, scan_ids, issue_links, issue_ids


def triage(repo: str, workflow: str, run_id: int | None, log_file: str | None = None) -> Triage:
    run = run_by_id(repo, run_id) if run_id is not None else latest_run(repo, workflow)
    actual_run_id = int(run["id"])
    jobs = run_jobs(repo, actual_run_id)
    failed_job = next((job for job in jobs if job.get("conclusion") == "failure"), jobs[0] if jobs else None)
    job_id = int(failed_job["id"]) if failed_job else None
    failed_step = None
    logs = ""
    notes: list[str] = []
    if failed_job:
        failed_step = next(
            (step.get("name") for step in failed_job.get("steps", []) if step.get("conclusion") == "failure"),
            None,
        )
        if log_file:
            with open(log_file, encoding="utf-8") as file:
                logs = file.read()
        else:
            try:
                logs = job_logs(repo, job_id)
            except urllib.error.HTTPError as error:
                notes.append(
                    f"Could not download job logs with the GitHub REST API: HTTP {error.code} {error.reason}. Set GITHUB_TOKEN/GH_TOKEN, use GitHub MCP logs, or pass --log-file."
                )

    errors, warnings, scan_ids, issue_links, issue_ids = parse_logs(logs)
    if any("dependency scan completed: found 0 new issues" in error for error in errors) and issue_links:
        notes.append(
            "The action reported zero dependency issues, but also emitted Aikido issue links. Treat this as a gate failure and inspect the linked issue type in Aikido."
        )

    return Triage(
        repo=repo,
        run_id=actual_run_id,
        run_url=run.get("html_url", ""),
        conclusion=run.get("conclusion"),
        job_id=job_id,
        failed_step=failed_step,
        classification=classify(logs, errors),
        scan_ids=scan_ids,
        issue_ids=issue_ids,
        issue_links=issue_links,
        errors=errors,
        warnings=warnings,
        notes=notes,
    )


def print_markdown(result: Triage) -> None:
    print(f"# Aikido Run Triage\n")
    print(f"- Repo: `{result.repo}`")
    print(f"- Run: [{result.run_id}]({result.run_url})")
    print(f"- Conclusion: `{result.conclusion}`")
    print(f"- Job ID: `{result.job_id}`")
    print(f"- Failed step: `{result.failed_step}`")
    print(f"- Classification: `{result.classification}`")
    if result.scan_ids:
        print(f"- Scan IDs: {', '.join(f'`{scan_id}`' for scan_id in result.scan_ids)}")
    if result.issue_ids:
        print(f"- Aikido issue IDs: {', '.join(f'`{issue_id}`' for issue_id in result.issue_ids)}")
    if result.issue_links:
        print("\n## Issue Links")
        for link in result.issue_links:
            print(f"- {link}")
    if result.errors:
        print("\n## Errors")
        for error in result.errors:
            print(f"- {error}")
    if result.warnings:
        print("\n## Warnings")
        for warning in result.warnings:
            print(f"- {warning}")
    if result.notes:
        print("\n## Notes")
        for note in result.notes:
            print(f"- {note}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repository in owner/name form")
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW, help="Workflow filename or ID")
    parser.add_argument("--run-id", type=int, help="Specific GitHub Actions run ID")
    parser.add_argument("--latest", action="store_true", help="Inspect the latest workflow run")
    parser.add_argument("--log-file", help="Parse a previously downloaded job log file")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    args = parser.parse_args()

    if args.run_id is None and not args.latest:
        parser.error("pass --run-id <id> or --latest")

    try:
        result = triage(args.repo, args.workflow, args.run_id, args.log_file)
    except urllib.error.HTTPError as error:
        print(f"GitHub API request failed: HTTP {error.code} {error.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"GitHub API request failed: {error.reason}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print_markdown(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
