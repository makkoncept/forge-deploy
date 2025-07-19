import yaml
from pathlib import Path

class Config:
    def __init__(self):
        self.config_path = Path.home() / '.config' / 'forge-deploy.yml'
        self.data = self._load_config()
        self._validate_config()
    
    def _load_config(self):
        if not self.config_path.exists():
            self._show_config_error()
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _show_config_error(self):
        print("Configuration file not found!")
        print(f"Expected location: {self.config_path}")
        print("\nPlease create the config file with the following structure:")
        print("=" * 60)
        print(self._get_sample_config())
        print("=" * 60)
    
    def _get_sample_config(self):
        """Return sample configuration from config.yml.example"""
        # Try to find config.yml.example in the parent directory (package root)
        package_root = Path(__file__).parent.parent
        example_file = package_root / 'config.yml.example'
        
        if example_file.exists():
            with open(example_file, 'r') as f:
                return f.read().strip()
        else:
            return 'Checkout the documentation for the correct config structure.'
            
    def _validate_config(self):
        required_keys = [
            'github.token',
            'local.qa_env_path'
        ]
        
        for key in required_keys:
            if not self._get_nested_value(key):
                raise ValueError(f"Missing required config key: {key}")
    
    def _get_nested_value(self, key_path):
        keys = key_path.split('.')
        value = self.data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    @property
    def github_token(self):
        return self.data['github']['token']
    
    @property
    def qa_env_path(self):
        return self.data['local']['qa_env_path']
    
    @property
    def polling_interval(self):
        return 30 # 30 seconds between action status checks
    
    @property
    def polling_timeout(self):
        return 1800 # 30 minutes max wait time