import requests
import time
import re
from datetime import datetime, timezone

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
    
    def _format_workflow_time(self, iso_timestamp: str) -> str:
        if not iso_timestamp:
            return "Unknown time"
        
        try:
            utc_dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
            local_dt = utc_dt.replace(tzinfo=timezone.utc).astimezone()
            return local_dt.strftime("%d-%m-%Y %H:%M:%S")
        except Exception:
            return iso_timestamp
    
    def _monitor_workflow(self, repo: str, branch: str, workflow_name: str, extract_tag: bool = False):
        print(f">> Looking for '{workflow_name}' workflow on branch '{branch}' in {repo}")
        workflow_run = self._get_latest_workflow_run(repo, branch, workflow_name)
        
        if not workflow_run:
            raise Exception(f"No '{workflow_name}' workflow found for branch {branch}")
        
        run_id = workflow_run['id']
        status = workflow_run.get('status')
        created_at = self._format_workflow_time(workflow_run.get('created_at'))
        updated_at = self._format_workflow_time(workflow_run.get('updated_at'))
        
        # Construct the workflow URL
        workflow_url = f"https://github.com/{repo}/actions/runs/{run_id}"
        
        print(f"Workflow found (created_at {created_at}) with status: {status}")
        print(f"Link: {workflow_url}")

        self._wait_for_workflow_completion(repo, run_id)
        
        if extract_tag:
            return self._extract_tag_from_workflow(repo, run_id)
    
    def monitor_qa_build(self, branch: str) -> str:        
        return self._monitor_workflow(self.hot_api_repo, branch, 'qa build', extract_tag=True)
    
    def monitor_spawn_action(self):        
        self._monitor_workflow(self.qa_env_repo, 'main', 'spawn changed/new areas', extract_tag=False)
    
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