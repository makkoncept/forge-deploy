# Forge Deploy

A CLI tool to automate QA deployments for forge environments. 

## Installation
### From PyPI (Recommended)

```bash
pip install forge-deploy
```

### From Source

```bash
git clone https://github.com/mayank-hiver/forge-deploy.git
cd forge-deploy
pip install -e .
```

## Configuration

Create a `forge-deploy.yml` file in `~/.config/`:

```yaml
github:
  token: "your_github_token_here" 

local:
  qa_env_path: "/path/to/your/qa-env"
```

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Create a new token with these permissions:
   - `repo` (Full control of private repositories)
   - `actions:read` (Read access to actions)
3. Copy the token to your config file

## Usage

### Basic Usage

```bash
forge-deploy --branch qa-feature-xyz --env hot-1
```

### Options

- `--branch`, `-b`: QA branch name (required)
- `--env`, `-e`: Environment to deploy to (e.g., hot-1, hot-2, hot-3) (required)  
- `--yes`, `-y`: Automatically approve commit without asking for confirmation

### Example Workflow

1. **Push your changes** to a QA branch (e.g., `qa-feature-xyz`)
2. **Run the tool**:
   ```bash
   forge-deploy -b qa-feature-xyz -e hot-1
   ```
3. The tool will:
   - Monitor the "qa build" GitHub Action
   - Extract the generated tag
   - Update the qa-env environment file with the new tag
   - Show you the diff and ask for confirmation (skips if tag already latest)
   - Push changes to main
   - Monitor the "spawn changed/new areas" action
   - Report when deployment is complete
