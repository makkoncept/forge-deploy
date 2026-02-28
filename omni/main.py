#!/usr/bin/env python3

import click
import os
import subprocess
import sys
import traceback

from omni.github_client import GitHubClient
from omni.config import Config

VALID_ENVS = ["hot-1", "hot-2", "hot-3", "hot-4", "hot-5", "hot-6"]


def get_current_branch():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise click.ClickException("Not inside a git repository or git is not installed")


def ensure_branch_pushed(branch):
    """Push the branch to origin if it doesn't exist on remote."""
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch],
        capture_output=True, text=True
    )
    if not result.stdout.strip():
        click.echo(f">> Branch '{branch}' not found on remote. Pushing...")
        subprocess.run(
            ["git", "push", "-u", "origin", branch],
            check=True
        )
        click.echo(f"   Pushed '{branch}' to origin")


def handle_error(e):
    click.echo(f"Error: {e}", err=True)
    if os.getenv('DEBUG'):
        traceback.print_exc()
    sys.exit(1)


@click.group()
def cli():
    """Omni - CLI tool for Hiver QA workflows."""
    pass


@cli.command()
@click.argument('env')
@click.option('--branch', '-b', default=None, help='Branch to deploy (defaults to current branch)')
@click.option('--qa', is_flag=True, default=False, help='Run QA automation after deployment')
def deploy(env, branch, qa):
    """Trigger a Forge Release Pipeline deployment.

    ENV is the target environment (hot-1 through hot-6).

    \b
    Examples:
        omni deploy hot-2
        omni deploy hot-2 -b feature/my-branch
        omni deploy hot-3 --qa
    """
    try:
        if env not in VALID_ENVS:
            raise click.ClickException(
                f"Invalid environment '{env}'. Must be one of: {', '.join(VALID_ENVS)}"
            )

        if branch is None:
            branch = get_current_branch()

        config = Config()
        client = GitHubClient(config.github_token)

        ensure_branch_pushed(branch)

        click.echo("=" * 60)
        click.echo(f">> Triggering Forge Release Pipeline")
        click.echo(f"   Branch : {branch}")
        click.echo(f"   Env    : {env}")
        click.echo(f"   QA Auto: {str(qa).lower()}")
        click.echo("=" * 60)

        inputs = {
            "areas": env,
            "run_build_deploy_qa": "true",
            "run_qa_automation": str(qa).lower(),
        }
        run_url = client.dispatch_and_monitor("hot-qa-cicd.yaml", branch, inputs)

        click.echo("=" * 60)
        click.echo("Deployment completed successfully!")
        click.echo(f"QA Dashboard: https://qa-dashboard.hiver.space/areas/{env}")
        click.echo("=" * 60)

    except click.ClickException:
        raise
    except Exception as e:
        handle_error(e)


@cli.command()
@click.option('--branch', '-b', default=None, help='Source branch (defaults to current branch)')
@click.option('--title', default='', help='PR title (auto-generated from branch name if empty)')
@click.option('--desc', default='', help='PR description')
def pr(branch, title, desc):
    """Create a PR for CodeReview via GitHub Actions.

    \b
    Examples:
        omni pr
        omni pr -b feature/my-branch
        omni pr --title "Fix login bug"
    """
    try:
        if branch is None:
            branch = get_current_branch()

        if branch == 'master':
            raise click.ClickException(
                "Source branch cannot be master"
            )

        config = Config()
        client = GitHubClient(config.github_token)

        ensure_branch_pushed(branch)

        # Check if branch has commits ahead of master
        result = subprocess.run(
            ["git", "rev-list", "--count", f"origin/master..origin/{branch}"],
            capture_output=True, text=True
        )
        if result.stdout.strip() == "0":
            raise click.ClickException(
                f"Branch '{branch}' has no commits ahead of master. Nothing to review."
            )

        click.echo("=" * 60)
        click.echo(f">> Triggering PR for CodeReview")
        click.echo(f"   Source : {branch}")
        click.echo(f"   Target : master")
        if title:
            click.echo(f"   Title  : {title}")
        click.echo("=" * 60)

        inputs = {
            "source_branch": branch,
            "target_branch": "master",
            "pr_title": title,
            "pr_description": desc,
        }
        client.dispatch_and_monitor("pr-for-codereview.yaml", branch, inputs)

        click.echo("=" * 60)
        click.echo("Code review PR created successfully!")
        click.echo("=" * 60)

    except click.ClickException:
        raise
    except Exception as e:
        handle_error(e)


if __name__ == '__main__':
    cli()
