# Coding template

This repository started out as a simple opinionated tsconfig.json template. However, there were a lot of things to be opinionated about so now it has setups for Oxlint, testing, package manager, CI/CD, web setup, traefik infrastructure, AI coding and more.

## Setup

- `npm install -g corepack`
- `corepack enable`
- `yarn install`
- `yarn test`

## Packages

### Simple function and test

Contains a simple function and unit testing to go with it.

### Traefik infrastructure

See separate [README.md](./packages/traefik-infrastructure/README.md).

### Web

Web infrastructure project with SolidJS and DaisyUI.

## Structure

- Using experimental TypeScript 7 version.
- Using Yarn as it simplifies adding arguments when running scripts.
- Using Zed instead of VS Code to keep the editor setup fast and avoid the performance cost and bloat.
- ESM-only.

### Oxlint

- Using Oxlint as the performance is immense compared to ESLint and the IDE plugin doesn't crash.
- The main downside is that customization of rules isn't yet possible and no linting of .json or other files.
- See `.zed/settings.json` for repository editor defaults.

### fnm

`fnm` is used and configured to automatically read the `.node-version` file and set the correct `node` version. See https://github.com/Schniz/fnm for more information.

### npm-check-updates

`npm-check-updates` helps automatically updating the dependencies in the project. Will most likely not be used in a real project because they can be very sensitive to updating dependencies, even minor ones.

### Aikido

Aikido is used for security scanning - https://www.aikido.dev/.

The repository is configured to check pull requests and only fails when new issues are introduced, not when existing issues are present.

If you want to fail on all issues you need to use the Aikido CLI - https://help.aikido.dev/container-image-scanning/local-image-scanning/pr-and-release-gating-using-local-image-scanner

### Codex hooks

This repository includes project-local Codex hooks under `.codex/`. To enable them,
start Codex from the CLI in this repository and approve the hooks with `/hooks`.
Hooks will not run until they have been reviewed and trusted in the CLI session.

### MCP

This repository configures the WebdriverIO MCP server for both Codex and Zed.
Codex reads the project-local server configuration from `.codex/config.toml` once
this repository is trusted. Zed reads the same server from `.zed/settings.json`;
reload or restart Zed if it does not pick up the setting immediately.

The first MCP startup may download `@wdio/mcp@latest` through `npx`.
