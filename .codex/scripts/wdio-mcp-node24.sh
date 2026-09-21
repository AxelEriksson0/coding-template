#!/usr/bin/env bash
set -euo pipefail

node_version="${WDIO_MCP_NODE_VERSION:-24.15.0}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(cd -- "${script_dir}/../.." && pwd)"
wdio_server="${WDIO_MCP_SERVER:-${repository_root}/node_modules/@wdio/mcp/lib/server.js}"

configure_linux_display_env() {
  [[ "$(uname -s)" == "Linux" ]] || return 0

  local user_id runtime_dir auth_file
  user_id="$(id -u)"
  runtime_dir="${XDG_RUNTIME_DIR:-/run/user/${user_id}}"

  if [[ -d "${runtime_dir}" ]]; then
    export XDG_RUNTIME_DIR="${runtime_dir}"

    if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -S "${runtime_dir}/bus" ]]; then
      export DBUS_SESSION_BUS_ADDRESS="unix:path=${runtime_dir}/bus"
    fi

    if [[ -z "${WAYLAND_DISPLAY:-}" && -S "${runtime_dir}/wayland-0" ]]; then
      export WAYLAND_DISPLAY="wayland-0"
    fi

    if [[ -z "${XAUTHORITY:-}" ]]; then
      auth_file="$(find "${runtime_dir}" -maxdepth 1 -name ".mutter-Xwaylandauth.*" -print -quit 2>/dev/null || true)"
      [[ -n "${auth_file}" ]] && export XAUTHORITY="${auth_file}"
    fi
  fi

  if [[ -z "${DISPLAY:-}" ]]; then
    export DISPLAY=":0"
  fi

  if [[ -z "${XDG_SESSION_TYPE:-}" ]]; then
    if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
      export XDG_SESSION_TYPE="wayland"
    else
      export XDG_SESSION_TYPE="x11"
    fi
  fi
}

configure_linux_display_env

if [[ ! -f "${wdio_server}" ]]; then
  cat >&2 <<EOF
The repository-local WebdriverIO MCP installation was not found.

Run pnpm install from ${repository_root}, or set WDIO_MCP_SERVER to the server entry point.
EOF
  exit 1
fi

if [[ -n "${WDIO_MCP_NODE:-}" ]]; then
  exec "${WDIO_MCP_NODE}" "${wdio_server}"
fi

if command -v fnm >/dev/null 2>&1; then
  exec fnm exec --using "${node_version}" node "${wdio_server}"
fi

if [[ -x "${HOME:-}/.local/share/fnm/fnm" ]]; then
  exec "${HOME}/.local/share/fnm/fnm" exec --using "${node_version}" node "${wdio_server}"
fi

node_major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || true)"
if [[ "${node_major}" == "24" ]]; then
  exec node "${wdio_server}"
fi

cat >&2 <<EOF
WebdriverIO MCP requires Node ${node_version} for Firefox/geckodriver sessions.

Install fnm, or set WDIO_MCP_NODE before starting Codex or Zed:
  WDIO_MCP_NODE=/path/to/node

The repository-local server is used by default. To override it, also set:
  WDIO_MCP_SERVER=/optional/path/to/@wdio/mcp/lib/server.js
EOF
exit 1
