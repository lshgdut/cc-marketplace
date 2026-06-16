#!/usr/bin/env bash
# bump-version.sh — single source of truth for the plugin version.
#
# Reads the version from .claude-plugin/plugin.json (canonical), bumps it
# according to the subcommand, and mirrors the new value into
# .claude-plugin/marketplace.json. Never commits — the developer reviews
# and commits.

set -euo pipefail

PLUGIN_JSON=".claude-plugin/plugin.json"
MARKET_JSON=".claude-plugin/marketplace.json"

die() { echo "bump-version: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing required tool: $1"; }

need jq

[[ -f "$PLUGIN_JSON" ]] || die "$PLUGIN_JSON not found"
[[ -f "$MARKET_JSON" ]] || die "$MARKET_JSON not found"

current() {
  jq -er '.version' "$PLUGIN_JSON"
}

bump() {
  local part="$1" cur major minor patch
  cur="$(current)"
  [[ "$cur" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]] \
    || die "current version '$cur' is not semver (major.minor.patch)"
  major="${BASH_REMATCH[1]}"
  minor="${BASH_REMATCH[2]}"
  patch="${BASH_REMATCH[3]}"

  case "$part" in
    patch) patch=$((patch + 1)) ;;
    minor) minor=$((minor + 1)); patch=0 ;;
    major) major=$((major + 1)); minor=0; patch=0 ;;
    *) die "unknown bump part: $part" ;;
  esac

  echo "${major}.${minor}.${patch}"
}

write_version() {
  local new="$1"
  tmp="$(mktemp)"
  jq --arg v "$new" '.version = $v' "$PLUGIN_JSON" > "$tmp"
  mv "$tmp" "$PLUGIN_JSON"

  tmp="$(mktemp)"
  jq --arg v "$new" '.plugins[0].version = $v' "$MARKET_JSON" > "$tmp"
  mv "$tmp" "$MARKET_JSON"
}

sync_only() {
  local cur mkt
  cur="$(current)"
  mkt="$(jq -er '.plugins[0].version' "$MARKET_JSON" 2>/dev/null || echo "")"
  if [[ "$cur" == "$mkt" ]]; then
    echo "bump-version: in sync ($cur)"
    exit 0
  fi
  echo "bump-version: syncing marketplace.json $mkt -> $cur"
  tmp="$(mktemp)"
  jq --arg v "$cur" '.plugins[0].version = $v' "$MARKET_JSON" > "$tmp"
  mv "$tmp" "$MARKET_JSON"
  exit 0
}

usage() {
  cat <<EOF
Usage: scripts/bump-version.sh <command>

Commands:
  patch           Bump patch version (1.0.2 -> 1.0.3)
  minor           Bump minor version (1.0.2 -> 1.1.0)
  major           Bump major version (1.0.2 -> 2.0.0)
  --show          Print the current version and exit
  --sync          Mirror plugin.json version into marketplace.json, then exit
  -h, --help      Show this help
EOF
}

case "${1:-}" in
  patch|minor|major)
    cur="$(current)"
    new="$(bump "$1")"
    write_version "$new"
    echo "bump-version: $cur -> $new"
    echo "bump-version: updated $PLUGIN_JSON and $MARKET_JSON"
    echo "bump-version: review the diff, then commit."
    ;;
  --show)
    current
    ;;
  --sync)
    sync_only
    ;;
  -h|--help|"")
    usage
    ;;
  *)
    usage >&2
    die "unknown command: $1"
    ;;
esac
