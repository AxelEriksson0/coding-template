# Technology decisions

This document records technologies that were evaluated but are not currently
used. A rejected technology is not permanently banned; its reconsideration
criteria describe when it may be worth evaluating again.

## Yarn

- **Status:** Rejected
- **Current choice:** pnpm
- **Reason:** Yarn repeatedly crashed while installing this workspace's
  dependencies. pnpm has provided reliable installs and supports the workspace
  catalog used to centralize dependency versions.
- **Reconsider when:** [Yarn 6](https://v6.yarnpkg.com/) is available as a stable
  release.
- **Acceptance criteria:** Verify clean and repeated installs, workspace command
  execution, lockfile reproducibility, dependency-version centralization, and CI
  behavior before replacing pnpm.

## Playwright MCP

- **Status:** Rejected for MCP browser automation
- **Current choice:** WebdriverIO MCP
- **Reason:** Playwright MCP did not work in the Fedora development environment
  used by this project, which was not an officially supported Playwright host
  when the MCP server was selected.
- **Reconsider when:** Playwright supports the development environment and a
  headed Firefox session works reliably.
- **Scope:** This decision only concerns the MCP server. The web workspace still
  uses Playwright Test for its end-to-end suite.
