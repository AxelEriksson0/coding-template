# Coding template

This repository started out as a simple opinionated tsconfig.json template. However, there were a lot of things to be opinionated about so now it has setups for Oxlint, testing, package manager, CI/CD, web setup, traefik infrastructure, AI coding and more.

## Setup

- `npm install -g corepack`
- `corepack enable`
- `pnpm install`
- `pnpm test`

## Packages

### Simple function and test

Contains a simple function and unit testing to go with it.

### Traefik infrastructure

See separate [README.md](./packages/traefik-infrastructure/README.md).

### Web

Web infrastructure project with SolidJS and DaisyUI.

## Structure

- Using experimental TypeScript 7 version.
- Using pnpm for fast, disk-efficient installs and workspace support.
- Using Zed instead of VS Code to keep the editor setup fast and avoid the performance cost and bloat.
- ESM-only.

See [technology decisions](./docs/TECHNOLOGY_DECISIONS.md) for rejected
alternatives and the criteria for reconsidering them.

### Oxlint

- Using Oxlint as the performance is immense compared to ESLint and the IDE plugin doesn't crash.
- The main downside is that customization of rules isn't yet possible and no linting of .json or other files.
- See `.zed/settings.json` for repository editor defaults.

### fnm

`fnm` is used and configured to automatically read the `.node-version` file and set the correct `node` version. See https://github.com/Schniz/fnm for more information.

### pnpm catalogs

Direct dependency versions are defined in the `catalog` section of `pnpm-workspace.yaml`. Package manifests reference those versions with the `catalog:` protocol. When adding a dependency, add its version to the catalog and use `"catalog:"` in the relevant `dependencies` or `devDependencies` section.

### Dependency updates

`pnpm update:dependencies` updates dependencies across the workspace to their latest versions, then deduplicates the resulting lockfile.

### Aikido

Aikido is used for security scanning - https://www.aikido.dev/.

The repository is configured to check pull requests and only fails when new issues are introduced, not when existing issues are present.

If you want to fail on all issues you need to use the Aikido CLI - https://help.aikido.dev/container-image-scanning/local-image-scanning/pr-and-release-gating-using-local-image-scanner

Codex can also use the Aikido MCP server configured in `.codex/config.toml`.
Create an Aikido MCP personal access token in Aikido, then expose it through
the shell environment that starts Codex:

```bash
# ~/.zshrc, ~/.bashrc, or another private shell startup file
export AIKIDO_API_KEY="your-aikido-token"
```

Do not commit this token in `.env`, `.codex/config.toml`, README examples with
real values, or any other tracked file. After updating your shell startup file,
run `source ~/.zshrc` or restart the terminal, then restart Codex. The
project-local MCP config forwards `AIKIDO_API_KEY` into the Aikido MCP server
with `env_vars`.

To let Codex list Aikido issues from the MCP server, enable the required MCP
permissions in Aikido at
https://app.aikido.dev/settings/integrations/ide/mcp/permissions. Issue feed
access also requires an Aikido subscription that includes this MCP feature.

### Codex hooks

This repository includes project-local Codex hooks under `.codex/`. To enable them,
start Codex from the CLI in this repository and approve the hooks with `/hooks`.
Hooks will not run until they have been reviewed and trusted in the CLI session.

### Agent configuration

Reusable AI-agent skills live under `.agents/skills/` so repository workflows
are not tied to a specific agent vendor. Keep agent-specific runtime
configuration in that agent's own directory, such as Codex MCP servers, hooks,
and launcher scripts under `.codex/`. See [`.codex/README.md`](./.codex/README.md)
for the MCP setup and its compatibility decisions.
