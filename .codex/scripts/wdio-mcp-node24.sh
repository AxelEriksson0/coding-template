#!/usr/bin/env bash
set -euo pipefail

node_version="${WDIO_MCP_NODE_VERSION:-24.15.0}"
wdio_package="${WDIO_MCP_PACKAGE:-@wdio/mcp@3.9.0}"

find_cached_wdio_server() {
  local npm_cache npx_cache
  npm_cache="${npm_config_cache:-${NPM_CONFIG_CACHE:-${HOME:-}/.npm}}"
  npx_cache="${npm_cache}/_npx"

  [[ -d "${npx_cache}" ]] || return 0

  find "${npx_cache}" -path "*/node_modules/@wdio/mcp/package.json" -print 2>/dev/null \
    | while IFS= read -r package_json; do
        node -e '
          const fs = require("node:fs");
          const packageJson = process.argv[1];
          const pkg = JSON.parse(fs.readFileSync(packageJson, "utf8"));
          console.log(`${pkg.version}\t${packageJson.replace(/\/package\.json$/, "/lib/server.js")}`);
        ' "${package_json}" 2>/dev/null || true
      done \
    | sort -Vr \
    | awk 'NR == 1 { print $2 }'
}

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

if [[ -n "${WDIO_MCP_NODE:-}" && -n "${WDIO_MCP_SERVER:-}" ]]; then
  exec "${WDIO_MCP_NODE}" "${WDIO_MCP_SERVER}"
fi

if command -v fnm >/dev/null 2>&1; then
  cached_server="$(find_cached_wdio_server)"
  if [[ -n "${cached_server}" && -f "${cached_server}" ]]; then
    exec fnm exec --using "${node_version}" node "${cached_server}"
  fi

  exec fnm exec --using "${node_version}" npx -y -p "${wdio_package}" wdio-mcp
fi

if [[ -x "${HOME:-}/.local/share/fnm/fnm" ]]; then
  cached_server="$(find_cached_wdio_server)"
  if [[ -n "${cached_server}" && -f "${cached_server}" ]]; then
    exec "${HOME}/.local/share/fnm/fnm" exec --using "${node_version}" node "${cached_server}"
  fi

  exec "${HOME}/.local/share/fnm/fnm" exec --using "${node_version}" npx -y -p "${wdio_package}" wdio-mcp
fi

node_major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || true)"
if [[ "${node_major}" == "24" ]]; then
  cached_server="$(find_cached_wdio_server)"
  if [[ -n "${cached_server}" && -f "${cached_server}" ]]; then
    exec node "${cached_server}"
  fi

  exec npx -y -p "${wdio_package}" wdio-mcp
fi

cat >&2 <<EOF
WebdriverIO MCP requires Node ${node_version} for Firefox/geckodriver sessions.

Install fnm, or set both of these environment variables before starting Codex or Zed:
  WDIO_MCP_NODE=/path/to/node
  WDIO_MCP_SERVER=/path/to/@wdio/mcp/lib/server.js
EOF
exit 1
