# Design Principles

## Focused Skills

Each skill should solve one problem well.

Examples:

* create merge request
* generate changelog
* analyze logs
* review migrations
* audit dependencies

Avoid giant multi-purpose workflows.

---

## Safe Defaults

Skills should:

* minimize destructive operations
* avoid force actions by default
* request confirmation when necessary
* use least-privilege tool access

---

## Maintainable Architecture

Skills should be:

* modular
* composable
* self-contained
* easy to review
* easy to extend

---

## Recommended Tooling

### Markdown Validation

```bash id="pnr4my"
markdownlint .
```

### YAML Validation

```bash id="ucm6ta"
yamllint .
```

### Formatting

```bash id="h8wb10"
prettier "**/*.md" --write
```

---

## CI Recommendations

Recommended automated checks:

* frontmatter validation
* markdown linting
* shell script validation
* broken link detection
* forbidden command scanning

---

## Security Notes

Skills may:

* execute shell commands
* modify repository files
* invoke external CLIs
* access git repositories

Always review third-party skills before installation.

Recommended practices:

* least-privilege tool access
* explicit allowed-tools
* avoid destructive defaults
* require confirmation for risky operations
