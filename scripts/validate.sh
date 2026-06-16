#!/usr/bin/env bash
# validate.sh — CI gate for the marketplace repo.
#
# Checks:
#   1. .claude-plugin/plugin.json and marketplace.json are valid JSON
#   2. Their version fields match (plugin.json is the source of truth)
#   3. Every skills/*/SKILL.md has YAML frontmatter with name + description
#   4. plugin.json has the required top-level fields
#
# Exits non-zero on the first failure.

set -euo pipefail

PLUGIN_JSON=".claude-plugin/plugin.json"
MARKET_JSON=".claude-plugin/marketplace.json"
SKILLS_DIR="skills"

die() { echo "validate: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing required tool: $1"; }
need jq

fail=0
note() { echo "validate: $*"; }
fail() { echo "validate: FAIL: $*" >&2; fail=1; }

# 1. JSON validity
for f in "$PLUGIN_JSON" "$MARKET_JSON"; do
  if ! jq -e . "$f" >/dev/null 2>&1; then
    fail "$f is not valid JSON"
  else
    note "ok: $f parses"
  fi
done

# 2. Version parity
if jq -e . "$PLUGIN_JSON" >/dev/null 2>&1 && jq -e . "$MARKET_JSON" >/dev/null 2>&1; then
  pv="$(jq -er '.version' "$PLUGIN_JSON")"
  mv="$(jq -er '.plugins[0].version' "$MARKET_JSON")"
  if [[ "$pv" != "$mv" ]]; then
    fail "version drift: plugin.json=$pv marketplace.json=$mv (run: make sync)"
  else
    note "ok: version in sync ($pv)"
  fi
fi

# 3. plugin.json required fields
if jq -e . "$PLUGIN_JSON" >/dev/null 2>&1; then
  for field in name description version; do
    val="$(jq -er --arg f "$field" '.[$f] // empty' "$PLUGIN_JSON" || true)"
    [[ -n "$val" ]] || fail "$PLUGIN_JSON missing required field: $field"
  done
fi

# 4. SKILL.md frontmatter
if [[ -d "$SKILLS_DIR" ]]; then
  while IFS= read -r -d '' skill; do
    name="$(awk '/^---$/{c++; next} c==1{print}' "$skill" | awk -F': *' '/^name:/{print $2; exit}')"
    desc="$(awk '/^---$/{c++; next} c==1{print}' "$skill" | awk -F': *' '/^description:/{$1=""; sub(/^ /,""); print; exit}')"
    if [[ -z "$name" ]]; then
      fail "$skill: frontmatter missing 'name'"
    else
      note "ok: $skill has name=$name"
    fi
    if [[ -z "$desc" ]]; then
      fail "$skill: frontmatter missing 'description'"
    fi
  done < <(find "$SKILLS_DIR" -name SKILL.md -print0)
fi

if (( fail )); then
  echo "validate: FAILED" >&2
  exit 1
fi
echo "validate: PASSED"
