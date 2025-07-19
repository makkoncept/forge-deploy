"""
Forge Deploy - A CLI tool to automate QA deployments for forge environments.
"""

__version__ = "0.1.0"
__author__ = "Mayank"
__email__ = "mayank.n@grexit.com"

from forge_deploy.main import deploy

__all__ = ["deploy"]