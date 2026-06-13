"""Project metrics API — real canister data from dfx + HTTP health."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.database.db import get_db
from app.models.project import Project
from app.services.canisterMetrics import (
    build_project_metrics,
    fetch_canister_metrics,
    format_bytes,
    format_cycles,
)

router = APIRouter(prefix="/api/v1", tags=["Metrics"])


async def _get_owned_project(
    project_id: int,
    user_id: int,
    db: AsyncSession,
) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _get_user_projects(user_id: int, db: AsyncSession) -> list[Project]:
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.updated_at.desc())
    )
    return list(result.scalars().all())


def _metrics_payload(project: Project) -> dict:
    metrics = build_project_metrics(
        canister_id=project.canister_id,
        url=project.url,
        code_content=project.code_content,
        project_name=project.name,
    )
    return {
        "success": True,
        "project_id": project.id,
        "project_name": project.name,
        "canister_id": project.canister_id,
        "url": project.url,
        "deployed_at": project.deployed_at.isoformat() if project.deployed_at else None,
        "metrics": metrics,
    }


@router.get("/projects/{project_id}/metrics")
async def get_project_metrics(
    project_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: AsyncSession = Depends(get_db),
):
    """Real canister metrics for a project (cycles, memory, HTTP health)."""
    project = await _get_owned_project(project_id, user_id, db)
    return _metrics_payload(project)


@router.get("/projects/{project_id}/metrics/live")
async def get_live_project_metrics(
    project_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: AsyncSession = Depends(get_db),
):
    """Alias for live metrics — same real data as /metrics."""
    project = await _get_owned_project(project_id, user_id, db)
    payload = _metrics_payload(project)
    return {"success": True, "live_data": payload["metrics"]}


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: AsyncSession = Depends(get_db),
):
    """Aggregated dashboard stats from real canister status."""
    projects = await _get_user_projects(user_id, db)
    deployed = [p for p in projects if p.canister_id]
    total_cycles = 0
    healthy = 0

    for project in deployed:
        metrics = fetch_canister_metrics(project.canister_id, project.url)
        total_cycles += metrics.get("cycles_balance", 0)
        if str(metrics.get("status", "")).lower() == "running":
            healthy += 1

    return {
        "success": True,
        "totalCanisters": len(deployed),
        "activeProjects": len([p for p in projects if p.status == "active"]),
        "totalCycles": total_cycles,
        "deploymentsThisMonth": len(deployed),
        "uptime": round((healthy / max(len(deployed), 1)) * 100, 1),
        "averageResponseTime": 0,
    }


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: AsyncSession = Depends(get_db),
):
    """Dashboard overview with real per-project canister metrics."""
    projects = await _get_user_projects(user_id, db)
    total_cycles = 0
    total_memory = 0
    healthy_projects = 0
    project_stats = []

    for project in projects:
        if project.canister_id:
            metrics = fetch_canister_metrics(project.canister_id, project.url)
            cycles = metrics.get("cycles_balance", 0)
            memory = metrics.get("memory_bytes", 0)
            is_healthy = str(metrics.get("status", "")).lower() == "running"
        else:
            cycles = 0
            memory = 0
            is_healthy = False

        total_cycles += cycles
        total_memory += memory
        if is_healthy:
            healthy_projects += 1

        project_stats.append(
            {
                "id": project.id,
                "name": project.name,
                "status": project.status,
                "canister_id": project.canister_id,
                "url": project.url,
                "cycles_balance": cycles,
                "memory_bytes": memory,
                "is_healthy": is_healthy,
                "created_at": project.created_at.isoformat(),
            }
        )

    deployed_count = len([p for p in projects if p.canister_id])
    return {
        "success": True,
        "overview": {
            "projects": {
                "total": len(projects),
                "active": len([p for p in projects if p.status == "active"]),
                "deployed": deployed_count,
                "healthy": healthy_projects,
                "health_percentage": round(
                    (healthy_projects / max(deployed_count, 1)) * 100, 1
                ),
            },
            "aggregated_metrics": {
                "total_cycles_balance": total_cycles,
                "total_cycles_formatted": format_cycles(total_cycles),
                "total_memory_bytes": total_memory,
                "total_memory_formatted": format_bytes(total_memory),
            },
            "recent_projects": project_stats[:6],
        },
    }


@router.get("/dashboard/canisters")
async def get_dashboard_canisters(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: AsyncSession = Depends(get_db),
):
    """List deployed canisters with real status."""
    projects = await _get_user_projects(user_id, db)
    canisters = []

    for project in projects:
        if not project.canister_id:
            continue
        metrics = fetch_canister_metrics(project.canister_id, project.url)
        canisters.append(
            {
                "id": project.id,
                "name": project.name,
                "canister_id": project.canister_id,
                "status": project.status,
                "url": project.url,
                "cycles_balance": metrics.get("cycles_balance", 0),
                "memory_bytes": metrics.get("memory_bytes", 0),
                "is_healthy": str(metrics.get("status", "")).lower() == "running",
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            }
        )

    return {"success": True, "data": canisters}


@router.get("/dashboard/activities")
async def get_dashboard_activities(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: AsyncSession = Depends(get_db),
):
    """Recent project activity from deployment timestamps."""
    from app.models.deployment import Deployment

    projects = await _get_user_projects(user_id, db)
    project_ids = [p.id for p in projects]
    if not project_ids:
        return {"success": True, "data": []}

    result = await db.execute(
        select(Deployment)
        .where(Deployment.project_id.in_(project_ids))
        .order_by(Deployment.created_at.desc())
        .limit(15)
    )
    deployments = result.scalars().all()
    project_by_id = {p.id: p for p in projects}

    activities = []
    for dep in deployments:
        project = project_by_id.get(dep.project_id)
        if not project:
            continue
        activities.append(
            {
                "id": f"dep_{dep.id}",
                "title": f"{project.name}: {dep.status}",
                "description": dep.message or dep.status,
                "timestamp": (dep.completed_at or dep.created_at).isoformat(),
                "status": dep.status,
                "project_id": dep.project_id,
                "deployment_id": dep.id,
            }
        )

    return {"success": True, "data": activities}
