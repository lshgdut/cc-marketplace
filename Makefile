SHELL := /usr/bin/env bash

PLUGIN_JSON := .claude-plugin/plugin.json
MARKET_JSON := .claude-plugin/marketplace.json

.PHONY: help validate sync bump-patch bump-minor bump-major show

help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

validate: ## Run all CI checks locally
	@bash scripts/validate.sh

sync: ## Mirror plugin.json version into marketplace.json
	@bash scripts/bump-version.sh --sync

show: ## Print current plugin version
	@bash scripts/bump-version.sh --show

bump-patch: ## Bump patch (1.0.2 -> 1.0.3)
	@bash scripts/bump-version.sh patch

bump-minor: ## Bump minor (1.0.2 -> 1.1.0)
	@bash scripts/bump-version.sh minor

bump-major: ## Bump major (1.0.2 -> 2.0.0)
	@bash scripts/bump-version.sh major
