import requests
import time
from datetime import datetime, timezone


class GitHubClient:
    def __init__(self, token, repo="Grexit/hot-api-mono"):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.repo = repo

    def dispatch_and_monitor(self, workflow_file, branch, inputs):
        """Trigger a workflow and monitor it until completion."""
        triggered_at = datetime.now(timezone.utc)
        self._dispatch_workflow(workflow_file, branch, inputs)
        print("Workflow dispatched. Waiting for it to appear...")
        time.sleep(5)

        run = self._find_triggered_run(workflow_file, branch, triggered_at)
        if not run:
            raise Exception(
                "Could not find the triggered workflow run. "
                "Check GitHub Actions manually."
            )

        run_id = run["id"]
        run_url = f"https://github.com/{self.repo}/actions/runs/{run_id}"
        print(f"Workflow run found: {run_url}")

        self._wait_for_completion(run_id)
        return run_url

    def _dispatch_workflow(self, workflow_file, branch, inputs):
        url = (
            f"{self.base_url}/repos/{self.repo}/actions/workflows/"
            f"{workflow_file}/dispatches"
        )
        payload = {
            "ref": branch,
            "inputs": inputs,
        }
        response = self._make_request("POST", url, json=payload)
        if response.status_code not in (204, 200):
            raise Exception(
                f"Failed to trigger workflow: {response.status_code} {response.text}"
            )

    def _find_triggered_run(self, workflow_file, branch, triggered_after, max_attempts=10):
        """Poll for the workflow run that was triggered after `triggered_after`."""
        url = f"{self.base_url}/repos/{self.repo}/actions/runs"
        params = {
            "branch": branch,
            "event": "workflow_dispatch",
            "per_page": 5,
        }

        for attempt in range(max_attempts):
            response = self._make_request("GET", url, params=params)
            runs = response.json().get("workflow_runs", [])

            for run in runs:
                created = datetime.fromisoformat(
                    run["created_at"].replace("Z", "+00:00")
                )
                if (
                    created >= triggered_after
                    and run.get("path", "").endswith(workflow_file)
                ):
                    return run

            time.sleep(3)

        return None

    def _wait_for_completion(self, run_id):
        url = f"{self.base_url}/repos/{self.repo}/actions/runs/{run_id}"

        while True:
            response = self._make_request("GET", url)
            data = response.json()
            status = data.get("status")
            conclusion = data.get("conclusion")

            if status == "completed":
                if conclusion == "success":
                    print("Workflow completed successfully!")
                    return
                else:
                    raise Exception(f"Workflow failed with conclusion: {conclusion}")

            print("Workflow still running, checking again in 30 seconds...")
            time.sleep(30)

    def find_pr_for_branch(self, branch):
        """Find an open PR for the given head branch."""
        url = f"{self.base_url}/repos/{self.repo}/pulls"
        params = {"head": f"{self.repo.split('/')[0]}:{branch}", "state": "open"}
        response = self._make_request("GET", url, params=params)
        pulls = response.json()
        if pulls:
            return pulls[0]["html_url"]
        return None

    def _make_request(self, method, url, **kwargs):
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method, url, headers=self.headers, **kwargs
                )
                if response.status_code != 204:
                    response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 401:
                    raise Exception(
                        "Authentication failed (401 Unauthorized).\n\n"
                        "Please check your GitHub token in ~/.config/omni.yml\n"
                        "The token needs 'repo' and 'workflow' scopes.\n\n"
                        "  github:\n"
                        "    token: \"ghp_your_token_here\""
                    )
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
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
