import git
import yaml
from pathlib import Path
import re

class GitOperations:
    def __init__(self, config):
        self.config = config
        self.repo_path = Path(config.qa_env_path)
        self.repo = git.Repo(self.repo_path)
    
    def update_env_file(self, env_name: str, tag: str):
        self._pull_latest_changes()
        
        env_file = self.repo_path / f"areas/{env_name}.yaml"
        
        if not env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {env_file}")
        
        # Read the file as text to preserve formatting otherwise YAML loader may alter it
        with open(env_file, 'r') as f:
            file_content = f.read()
        
        # Also load as YAML to validate structure and get current tag
        with open(env_file, 'r') as f:
            env_data = yaml.safe_load(f)
        
        if 'modules' not in env_data:
            raise KeyError(f"'modules' section not found in {env_file}")
        
        hot_module = None
        for module in env_data['modules']:
            if module.get('name') == 'hot':
                hot_module = module
                break
        
        if not hot_module:
            raise KeyError(f"'hot' module not found in {env_file}")
        
        if 'services' not in hot_module:
            raise KeyError(f"'services' section not found in hot module")
        
        # Find hot-api-mono service and get current tag
        hot_api_service = None
        for service in hot_module['services']:
            if service.get('name') == 'hot-api-mono':
                hot_api_service = service
                break
        
        if not hot_api_service:
            raise KeyError(f"'hot-api-mono' service not found in hot module")
        
        old_tag = hot_api_service.get('tag', 'unknown')
        
        if old_tag == tag:
            print(f"Tag is already up to date: {tag}")
            print(f"   No changes needed for {env_file}")
            return False
        
        # Use regex to find and replace the hot-api-mono tag while preserving formatting
        # Look for the hot-api-mono service and its tag line
        pattern = r'(\s+- name: hot-api-mono\s+tag:\s+)([^\s\n]+)'
        
        def replace_tag(match):
            return match.group(1) + tag
        
        new_content = re.sub(pattern, replace_tag, file_content)
        
        if new_content == file_content:
            raise Exception("Could not find hot-api-mono tag to update")
        
        with open(env_file, 'w') as f:
            f.write(new_content)
        
        return True
    
    def _pull_latest_changes(self):
        try:
            # qa-env works on main branch
            self.repo.git.checkout('main')
            
            self.repo.git.pull('origin', 'main')
            
            print("Pulled latest changes from main")
        except Exception as e:
            print(f"Warning: Could not pull latest changes: {e}")
    
    def show_diff(self):
        try:
            diff = self.repo.git.diff('--color=always')
            if diff:
                print(diff)
            else:
                print("No changes detected")
        except Exception as e:
            print(f"Error showing diff: {e}")
    
    def reset_changes(self):
        try:
            self.repo.git.checkout('--', '.')
            print("All changes have been reset")
        except Exception as e:
            print(f"Error resetting changes: {e}")
    
    def push_to_main(self):
        self.repo.git.add('.')
        
        if self.repo.is_dirty():
            self.repo.git.commit('-m', 'Update environment with new tag')
            
            self.repo.git.push('origin', 'main')
        else:
            print("No changes to commit")