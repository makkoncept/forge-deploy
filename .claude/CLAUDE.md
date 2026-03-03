# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Omni (formerly forge-deploy) is a Python CLI tool for Hiver QA workflows. It automates deployment to Forge QA environments and PR creation for code review, integrating with GitHub Actions on the `Grexit/hot-api-mono` repository.

## Build & Run Commands

```bash
# Install in development mode
pip install -e .

# Install globally (recommended)
pipx install -e .

# Run CLI
omni deploy hot-2                          # Deploy current branch to hot-2
omni deploy hot-2 -b feature/my-branch     # Deploy specific branch
omni deploy hot-3 --qa                     # Deploy with QA flag
omni pr                                    # Create PR for current branch
omni pr --title "Fix login bug" --desc "Details"  # PR with title/description
```

There are no tests, linting, or CI configured for this repository.

## Architecture

**Entry point**: `omni/main.py:cli` — Click-based CLI group with two commands: `deploy` and `pr`.

**Three-file structure**:
- `omni/main.py` — CLI commands, git operations (via subprocess), input validation. Valid deploy environments: hot-1 through hot-6.
- `omni/github_client.py` — `GitHubClient` class wrapping the GitHub Actions API. Dispatches workflows (`hot-qa-cicd.yaml`, `pr-for-codereview.yaml`) and polls for completion with exponential backoff retry logic.
- `omni/config.py` — `Config` class loading GitHub token from `~/.config/omni.yml` (YAML format).

**Key patterns**:
- GitHub workflow monitoring uses polling: 3-second intervals to find triggered runs, 30-second intervals to wait for completion.
- HTTP requests use 3-attempt retry with exponential backoff.
- The target GitHub repo (`Grexit/hot-api-mono`) is hardcoded in `github_client.py`.
- `DEBUG` environment variable enables verbose error output.

**Notes**
- The hiver repositories exists in `~/hiver/*` (eg: `~/hiver/hot-api-mono`, `~/hiver/hot-super-admin`). 
- Before running the `gh` commands (eg: for fetching github workflows), make sure that you switch to work profile (`mayank-hiver`). If the work profile does not exists, stop and ask the user to add it.
