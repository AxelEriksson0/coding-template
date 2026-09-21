# Repository Guidelines

## Project Structure & Module Organization

This is a pnpm workspace monorepo. The root contains shared tooling and repository configuration, including `package.json`, `pnpm-workspace.yaml`, `tsconfig.json`, `.oxlintrc.json`, `.github/workflows/`, and `lefthook.yml`.

- `packages/simple-function-and-test/`: small TypeScript package with source in `index.ts` and `utils/`, plus unit tests in `tests/`.
- `packages/web/`: SolidJS/Vite web app. Source lives in `src/`, browser tests in `tests/`, locale messages in `messages/`, and static assets in `src/assets/`.
- `packages/*-infrastructure/`: infrastructure documentation and deployment scripts; these are not currently pnpm workspaces.
- `docs/`: supporting notes about project decisions and TypeScript configuration.

## Build, Test, and Development Commands

Run commands from the repository root unless noted.

- `pnpm build`: builds all workspaces that define a build script.
- `pnpm lint`: runs Oxlint with type-aware checks.
- `pnpm format`: formats the repository with Oxfmt.
- `pnpm ut`: runs workspace unit test scripts.
- `pnpm test`: runs format, lint, and unit tests.
- `pnpm --filter web start`: starts the Vite dev server.
- `pnpm --filter web e2e`: runs Playwright tests for the web app.

## Dependency Management

Declare dependency versions in the `catalog` section of `pnpm-workspace.yaml`, including dependencies used only by the root package. Reference cataloged dependencies from `package.json` files with `"catalog:"` instead of repeating version numbers in individual manifests. Keep `pnpm-lock.yaml` updated whenever catalog entries or dependency references change.

## Coding Style & Naming Conventions

Use TypeScript and ESM imports. Keep package code strict and explicit; avoid unused locals, unused parameters, implicit returns, and console logging outside intentional CLI/demo entry points. Formatting is handled by Oxfmt, and linting is handled by Oxlint.

Use PascalCase for Solid components, for example `LanguageToggle.tsx`, and camelCase for functions such as `addTwoNumbers`. Keep tests close to the package they verify under a `tests/` directory.

## Testing Guidelines

The simple TypeScript package uses Node’s built-in test runner with `node:test` and `node:assert/strict`. Name unit tests `*.test.ts`. The web package uses Playwright with specs named `*.spec.ts`.

Codex runs `pnpm lint`, `pnpm build`, and `pnpm ut` automatically through project-local `PostToolUse` hooks after edit tools are used. Run `pnpm --filter web e2e` when changing browser behavior, routing, localization, or visible UI.

## Commit & Pull Request Guidelines

Recent history mostly uses concise Conventional Commit prefixes such as `feat:`, `fix:`, `chore:`, and `refactor:`. Keep commit subjects short but descriptive, for example `fix: update language toggle test setup`.

Pull requests should include a brief summary, the checks run, linked issues when applicable, and screenshots or recordings for UI changes. Mention any skipped checks with the reason.

## Security & Configuration Tips

Do not commit `.env` files or secrets. Use `.env.example` files for documented configuration. Be careful with deployment scripts under infrastructure packages; note target hosts, required tools, and manual steps in the relevant package README.
