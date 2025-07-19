import requests
import time
import re

class GitHubClient:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.hot_api_repo = "Grexit/hot-api-mono"
        self.qa_env_repo = "Grexit/qa-env"
    
    def monitor_qa_build(self, branch: str) -> str:        
        print(f"Looking for 'qa build' workflow on branch '{branch}' in {self.hot_api_repo}")
        workflow_run = self._get_latest_workflow_run(self.hot_api_repo, branch, 'qa build')
        
        if not workflow_run:
            raise Exception(f"No 'qa build' workflow found for branch {branch}")
        
        run_id = workflow_run['id']
        print(f"Found workflow run {run_id} with status: {workflow_run.get('status')}")
        self._wait_for_workflow_completion(self.hot_api_repo, run_id)
        
        tag = self._extract_tag_from_workflow(self.hot_api_repo, run_id)
        
        return tag
    
    def monitor_spawn_action(self):        
        workflow_run = self._get_latest_workflow_run(self.qa_env_repo, 'main', 'spawn changed/new areas')
        
        if not workflow_run:
            raise Exception("No 'spawn changed/new areas' workflow found")
        
        run_id = workflow_run['id']
        self._wait_for_workflow_completion(self.qa_env_repo, run_id)
    
    def _get_latest_workflow_run(self, repo: str, branch: str, workflow_name: str):
        url = f"{self.base_url}/repos/{repo}/actions/runs"
        params = {
            "branch": branch,
            "per_page": 10
        }
        
        response = self._make_request("GET", url, params=params)
        
        runs = response.json().get('workflow_runs', [])
        for run in runs:
            if run.get('name').lower() == workflow_name.lower():
                return run
        
        return None
    
    def _wait_for_workflow_completion(self, repo: str, run_id: int):
        url = f"{self.base_url}/repos/{repo}/actions/runs/{run_id}"
        
        while True:
            try:
                response = self._make_request("GET", url)
                run_data = response.json()
                
                status = run_data.get('status')
                conclusion = run_data.get('conclusion')
                
                if status == 'completed':
                    if conclusion == 'success':
                        print("Workflow completed successfully")
                        return True
                    else:
                        print(f"Workflow failed with conclusion: {conclusion}")
                        return False
                
                print("Workflow still running, checking again in 30 seconds...")
                time.sleep(30)
                
            except Exception as e:
                print(f"Error checking workflow status: {e}")
                print("Retrying in 30 seconds...")
                time.sleep(30)
    
    def _extract_tag_from_workflow(self, repo: str, run_id: int) -> str:
        url = f"{self.base_url}/repos/{repo}/actions/runs/{run_id}/jobs"
        response = self._make_request("GET", url)
        
        jobs = response.json()['jobs']
        
        for job in jobs:
            job_id = job['id']
            
            logs_url = f"{self.base_url}/repos/{repo}/actions/jobs/{job_id}/logs"
            try:
                logs_response = self._make_request("GET", logs_url)
                if logs_response.status_code == 200:
                    logs = logs_response.text

                    # Look for the tag pattern (e.g., v-qa-xxxx...)
                    tag_match = re.search(r'v-qa-[a-f0-9]{4,}', logs)
                    if tag_match:
                        return tag_match.group(0)
            except Exception as e:
                continue
        
        raise Exception("Could not extract tag from workflow logs")
    
    def _make_request(self, method: str, url: str, **kwargs):
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                session = requests.Session()
                session.headers.update(self.headers)
                
                response = session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise