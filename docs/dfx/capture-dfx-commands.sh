#!/usr/bin/env bash
# Capture dfx --help (and safe command output) into docs/dfx/<path>/response.txt
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/docs/dfx"
DFX_VERSION="$(dfx --version 2>&1)"
GENERATED="$(date -Iseconds)"

mkdir -p "$OUT"

parse_subcommands() {
  awk '
    /^Commands:/ { in_cmds=1; next }
    /^Options:/ { in_cmds=0 }
    in_cmds && /^  [a-zA-Z0-9_-]+/ {
      name=$1
      if (name != "help") print name
    }
  '
}

safe_run() {
  local -a parts=("$@")
  local key="${parts[*]}"
  key="${key// /\/}"

  case "$key" in
    "")
      dfx --version 2>&1 && echo "---" && dfx --help 2>&1 | head -5
      ;;
    info)
      (cd "$ROOT" && dfx info 2>&1)
      ;;
    ping)
      (cd "$ROOT" && dfx ping ic 2>&1)
      ;;
    schema)
      (cd "$ROOT" && dfx schema 2>&1)
      ;;
    diagnose)
      (cd "$ROOT" && dfx diagnose 2>&1)
      ;;
    identity/list)
      dfx identity list 2>&1
      ;;
    identity/whoami)
      dfx identity whoami 2>&1
      ;;
    identity/get-principal)
      dfx identity get-principal 2>&1
      ;;
    extension/list)
      dfx extension list 2>&1
      ;;
    cache/show)
      dfx cache show 2>&1
      ;;
    *)
      return 1
      ;;
  esac
}

capture_help() {
  local rel_path="$1"
  shift
  local -a parts=("$@")

  local help_out run_out
  help_out="$(dfx "${parts[@]}" --help 2>&1)" || help_out="(exit $?) $help_out"

  run_out=""
  if run_out="$(safe_run "${parts[@]}" 2>&1)"; then
    :
  else
    run_out=""
  fi

  mkdir -p "$OUT/$rel_path"
  {
    echo "# dfx ${parts[*]} --help"
    echo "# Generated: $GENERATED"
    echo "# dfx: $DFX_VERSION"
    echo ""
    echo "=== SUPPORT (--help) ==="
    echo "$help_out"
    if [[ -n "$run_out" ]]; then
      echo ""
      echo "=== RESPONSE (safe run) ==="
      echo "$run_out"
    fi
  } > "$OUT/$rel_path/response.txt"
}

walk() {
  local rel_path="$1"
  shift
  local -a parts=("$@")

  capture_help "$rel_path" "${parts[@]}"

  local subs
  subs="$(dfx "${parts[@]}" --help 2>&1 | parse_subcommands)" || true

  while IFS= read -r sub; do
    [[ -z "$sub" ]] && continue
    local next_path
    if [[ "$rel_path" == "_root" ]]; then
      next_path="$sub"
    else
      next_path="$rel_path/$sub"
    fi
    walk "$next_path" "${parts[@]}" "$sub"
  done <<< "$subs"
}

echo "Capturing dfx commands to $OUT ..."
walk "_root"
count="$(find "$OUT" -name 'response.txt' | wc -l)"
echo "Done. $count response files under docs/dfx/"
