import yaml
from pathlib import Path


class Config:
    def __init__(self):
        self.config_path = Path.home() / '.config' / 'omni.yml'
        self.data = self._load_config()
        self._validate_config()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n\n"
                f"Create it with:\n"
                f"  mkdir -p ~/.config\n"
                f"  cat > {self.config_path} << 'EOF'\n"
                f"github:\n"
                f"  token: \"your_github_token_here\"\n"
                f"EOF"
            )

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _validate_config(self):
        if not self.data or 'github' not in self.data or 'token' not in self.data['github']:
            raise ValueError("Missing required config key: github.token")

    @property
    def github_token(self):
        return self.data['github']['token']
