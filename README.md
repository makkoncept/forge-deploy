# Omni

CLI tool for Hiver QA workflows.

## Installation

```bash
git clone https://github.com/mayank-hiver/forge-deploy.git
cd forge-deploy
pip install -e .
```

### Global Install (Recommended)

Use [pipx](https://pipx.pypa.io/) to install globally without managing venvs:

```bash
brew install pipx
pipx ensurepath
pipx install -e .          # editable: picks up code changes automatically
```

## Configuration

Create `~/.config/omni.yml`:

```yaml
github:
  token: "your_github_token_here"
```

You'll need a GitHub token with `repo` and `actions:read` permissions.

## Usage

### Deploy to Forge

```bash
omni deploy hot-2                        # deploy current branch
omni deploy hot-2 -b feature/my-branch   # deploy a specific branch
omni deploy hot-3 --qa                   # deploy and run QA automation
```

**Environments:** hot-1 through hot-6

### Create a PR for Code Review

```bash
omni pr                                  # PR from current branch
omni pr -b feature/my-branch             # PR from a specific branch
omni pr --title "Fix login bug"          # PR with a custom title
omni pr --desc "Details here"            # PR with a description
```
