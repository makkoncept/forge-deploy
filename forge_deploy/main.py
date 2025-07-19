#!/usr/bin/env python3

import click
import os
import sys
import traceback

from forge_deploy.github_client import GitHubClient
from forge_deploy.git_operations import GitOperations
from forge_deploy.config import Config

@click.command()
@click.option('--branch', '-b', required=True, help='QA branch name (e.g., qa-feature-xyz)')
@click.option('--env', '-e', required=True, help='Environment to deploy to (e.g., hot-1, hot-2, hot-3)')
def deploy(branch, env):
    try:
        config_obj = Config()
        
        github_client = GitHubClient(config_obj.github_token)
        git_ops = GitOperations(config_obj)
        
        click.echo(f"Starting QA deployment of branch '{branch}' to environment '{env}'")
        
        click.echo("Monitoring 'qa build' action...")
        tag = github_client.monitor_qa_build(branch)
        click.echo(f"Build completed! Tag: {tag}")
        
        click.echo(f"Updating {env}.yaml with tag {tag}...")
        changes_made = git_ops.update_env_file(env, tag)
        
        if not changes_made:
            click.echo("Tag is already up to date - skipping to deployment monitoring...")
        else:
            click.echo("\nChanges made:")
            git_ops.show_diff()
            
            if click.confirm("\nDo you want to commit and push these changes?"):
                click.echo("Pushing changes to main...")
                git_ops.push_to_main()
            else:
                click.echo("Deployment cancelled by user")
                if click.confirm("Do you want to discard the changes?"):
                    git_ops.reset_changes()
                    click.echo("Changes discarded")
                return
        
        click.echo("Monitoring 'spawn changed/new area' action...")
        github_client.monitor_spawn_action()
        
        click.echo("Deployment completed successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if os.getenv('DEBUG'):
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    deploy()