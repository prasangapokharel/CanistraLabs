"""Celery tasks module."""

# Import tasks to register them
from app.tasks.celeryApp import celery_app  # noqa: F401
from app.tasks.deployment import check_canister_status_task, deploy_project_task  # noqa: F401

__all__ = ["celery_app", "deploy_project_task", "check_canister_status_task"]
