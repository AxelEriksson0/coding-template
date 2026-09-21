# Codex configuration

This directory contains the repository-local Codex configuration, hooks, and
launcher scripts.

## Browser automation MCP

This repository uses WebdriverIO MCP for interactive browser automation by
agents. Codex reads the server configuration from `config.toml` after the
repository is trusted. Zed configures the same server in `../.zed/settings.json`.
Both clients start the shared launcher at `scripts/wdio-mcp-node24.sh`.

### Node 24 compatibility pin

WebdriverIO MCP is intentionally pinned to Node 24.15.0 because its
Firefox/geckodriver sessions fail when launched with newer Node versions. This
pin only applies to the MCP process; the rest of the repository uses the Node
version declared in `../package.json`.

Do not update or remove the MCP pin until a headed Firefox session has been
verified with the replacement version.

The `@wdio/mcp` version is declared in the catalog in `../pnpm-workspace.yaml`,
referenced from the root `package.json`, and locked by `pnpm-lock.yaml`. The
launcher uses `fnm exec --using 24.15.0` to start that repository-local
installation. Run `pnpm install` before starting Codex or Zed. If another Node
manager is used, set `WDIO_MCP_NODE`; `WDIO_MCP_SERVER` can optionally override
the repository-local server entry point.

The `wdio-mcp` shim is not called directly because its `env node` shebang can
resolve to a newer active Node version and break Firefox/geckodriver sessions.
On Linux, the launcher also restores missing desktop session environment
variables required by headed Firefox.

### Why not Playwright MCP?

The MCP choice was made for the Fedora development environment used by this
project. Playwright MCP did not work there, and Fedora was not an officially
supported Playwright host when this setup was selected. WebdriverIO MCP was
therefore chosen for agent-driven browser automation.

This decision only concerns the MCP server. The web workspace still uses
Playwright Test for its E2E suite through `pnpm --filter web e2e`.
