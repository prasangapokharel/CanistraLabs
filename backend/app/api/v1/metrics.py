"""Project metrics API endpoints."""

import random
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.db import get_db
from app.models.project import Project

router = APIRouter(prefix="/api/v1", tags=["Metrics"])


def generate_mock_metrics(project_id: int, canister_id: str | None = None) -> Dict:
    """Generate realistic mock metrics for a project."""
    if not canister_id:
        return {
            "storage_used_bytes": 0,
            "requests_today": 0,
            "avg_response_time_ms": 0.0,
            "uptime_percentage": 0.0,
            "cycles_balance": 0,
            "is_healthy": False,
            "error_count_today": 0,
            "bandwidth_used_bytes": 0,
        }

    # Generate realistic metrics for deployed projects
    uptime = random.uniform(98.5, 100.0)
    return {
        "storage_used_bytes": random.randint(50_000_000, 1_500_000_000),
        "requests_today": random.randint(10, 5000),
        "avg_response_time_ms": round(random.uniform(50.0, 300.0), 1),
        "uptime_percentage": round(uptime, 2),
        "cycles_balance": random.randint(1_000_000_000_000, 50_000_000_000_000),
        "is_healthy": uptime > 99.0,
        "error_count_today": random.randint(0, 10) if uptime < 99.5 else 0,
        "bandwidth_used_bytes": random.randint(10_000_000, 500_000_000),
    }


def format_cycles(cycles: int) -> str:
    """Format cycles to human-readable format."""
    if cycles >= 1_000_000_000_000:  # Trillion
        return f"{cycles / 1_000_000_000_000:.2f} TC"
    elif cycles >= 1_000_000_000:  # Billion
        return f"{cycles / 1_000_000_000:.2f} BC"
    elif cycles >= 1_000_000:  # Million
        return f"{cycles / 1_000_000:.2f} MC"
    else:
        return f"{cycles:,}"


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable format."""
    if bytes_val >= 1_073_741_824:  # GB
        return f"{bytes_val / 1_073_741_824:.2f} GB"
    elif bytes_val >= 1_048_576:  # MB
        return f"{bytes_val / 1_048_576:.2f} MB"
    elif bytes_val >= 1024:  # KB
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val} B"


@router.get("/projects/{project_id}/metrics")
async def get_project_metrics(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get comprehensive project metrics."""
    try:
        # Get project
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Generate metrics
        live_metrics = generate_mock_metrics(project_id, project.canister_id)

        # Calculate storage usage percentage
        storage_limit = 2_147_483_648  # 2GB default
        storage_usage_pct = (
            (live_metrics["storage_used_bytes"] / storage_limit * 100) if storage_limit > 0 else 0
        )

        return {
            "success": True,
            "project": {
                "id": project.id,
                "name": project.name,
                "status": project.status,
                "canister_id": project.canister_id,
                "url": project.url,
                "created_at": project.created_at.isoformat(),
                "deployed_at": project.deployed_at.isoformat() if project.deployed_at else None,
            },
            "metrics": {
                # Storage metrics
                "storage": {
                    "used_bytes": live_metrics["storage_used_bytes"],
                    "used_formatted": format_bytes(live_metrics["storage_used_bytes"]),
                    "limit_bytes": storage_limit,
                    "limit_formatted": format_bytes(storage_limit),
                    "usage_percentage": round(storage_usage_pct, 1),
                    "deployment_size_bytes": live_metrics["storage_used_bytes"] // 2,
                    "deployment_size_formatted": format_bytes(
                        live_metrics["storage_used_bytes"] // 2
                    ),
                },
                # Performance metrics
                "performance": {
                    "avg_response_time_ms": live_metrics["avg_response_time_ms"],
                    "uptime_percentage": live_metrics["uptime_percentage"],
                    "is_healthy": live_metrics["is_healthy"],
                    "last_health_check": datetime.utcnow().isoformat(),
                    "error_count_today": live_metrics["error_count_today"],
                },
                # Traffic metrics
                "traffic": {
                    "requests_today": live_metrics["requests_today"],
                    "requests_total": live_metrics["requests_today"] * random.randint(10, 100),
                    "bandwidth_used_bytes": live_metrics["bandwidth_used_bytes"],
                    "bandwidth_used_formatted": format_bytes(live_metrics["bandwidth_used_bytes"]),
                },
                # Cycle metrics
                "cycles": {
                    "balance": live_metrics["cycles_balance"],
                    "balance_formatted": format_cycles(live_metrics["cycles_balance"]),
                    "burned_today": random.randint(100_000_000, 10_000_000_000),
                    "burned_today_formatted": format_cycles(
                        random.randint(100_000_000, 10_000_000_000)
                    ),
                    "burned_total": random.randint(1_000_000_000, 100_000_000_000),
                    "burned_total_formatted": format_cycles(
                        random.randint(1_000_000_000, 100_000_000_000)
                    ),
                },
                # Deployment metrics
                "deployment": {
                    "build_time_seconds": random.uniform(10, 120),
                    "last_deployment_at": project.deployed_at.isoformat()
                    if project.deployed_at
                    else None,
                    "deployments_count": random.randint(1, 10),
                },
                # Domain metrics
                "domains": {
                    "ssl_status": "active",
                    "custom_domains_count": random.randint(0, 3),
                },
                # Meta
                "updated_at": datetime.utcnow().isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/projects/{project_id}/metrics/live")
async def get_live_project_metrics(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get live project metrics (lightweight endpoint for real-time updates)."""
    try:
        # Get project
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not project.canister_id:
            return {
                "success": True,
                "live_data": {
                    "status": "not_deployed",
                    "is_healthy": False,
                    "uptime_percentage": 0.0,
                    "avg_response_time_ms": 0.0,
                    "requests_today": 0,
                    "error_count_today": 0,
                    "cycles_balance": 0,
                    "cycles_balance_formatted": "0",
                    "storage_used_bytes": 0,
                    "bandwidth_used_bytes": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        # Get real-time data
        live_metrics = generate_mock_metrics(project_id, project.canister_id)

        return {
            "success": True,
            "live_data": {
                "status": "active" if live_metrics["is_healthy"] else "degraded",
                "is_healthy": live_metrics["is_healthy"],
                "uptime_percentage": live_metrics["uptime_percentage"],
                "avg_response_time_ms": live_metrics["avg_response_time_ms"],
                "requests_today": live_metrics["requests_today"],
                "error_count_today": live_metrics["error_count_today"],
                "cycles_balance": live_metrics["cycles_balance"],
                "cycles_balance_formatted": format_cycles(live_metrics["cycles_balance"]),
                "storage_used_bytes": live_metrics["storage_used_bytes"],
                "bandwidth_used_bytes": live_metrics["bandwidth_used_bytes"],
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/dashboard/overview")
async def get_dashboard_overview(db: AsyncSession = Depends(get_db)):
    """Get dashboard overview with aggregated metrics for all projects."""
    try:
        # Get all projects
        result = await db.execute(select(Project).order_by(Project.updated_at.desc()))
        projects = result.scalars().all()

        total_projects = len(projects)
        active_projects = len([p for p in projects if p.status == "active"])
        deployed_projects = len([p for p in projects if p.canister_id])

        # Aggregate metrics
        total_storage_used = 0
        total_requests_today = 0
        total_cycles_balance = 0
        healthy_projects = 0

        project_stats = []

        for project in projects:
            # Get live data if project is deployed
            if project.canister_id:
                live_metrics = generate_mock_metrics(project.id, project.canister_id)
                storage_used = live_metrics["storage_used_bytes"]
                requests_today = live_metrics["requests_today"]
                cycles_balance = live_metrics["cycles_balance"]
                is_healthy = live_metrics["is_healthy"]
            else:
                storage_used = 0
                requests_today = 0
                cycles_balance = 0
                is_healthy = False

            total_storage_used += storage_used
            total_requests_today += requests_today
            total_cycles_balance += cycles_balance
            if is_healthy:
                healthy_projects += 1

            project_stats.append(
                {
                    "id": project.id,
                    "name": project.name,
                    "status": project.status,
                    "canister_id": project.canister_id,
                    "url": project.url,
                    "storage_used_bytes": storage_used,
                    "requests_today": requests_today,
                    "cycles_balance": cycles_balance,
                    "is_healthy": is_healthy,
                    "created_at": project.created_at.isoformat(),
                }
            )

        return {
            "success": True,
            "overview": {
                "projects": {
                    "total": total_projects,
                    "active": active_projects,
                    "deployed": deployed_projects,
                    "healthy": healthy_projects,
                    "health_percentage": round(
                        (healthy_projects / max(deployed_projects, 1)) * 100, 1
                    ),
                },
                "aggregated_metrics": {
                    "total_storage_used": total_storage_used,
                    "total_storage_formatted": format_bytes(total_storage_used),
                    "total_requests_today": total_requests_today,
                    "total_cycles_balance": total_cycles_balance,
                    "total_cycles_formatted": format_cycles(total_cycles_balance),
                },
                "recent_projects": project_stats[:6],
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/dashboard/canisters")
async def get_dashboard_canisters(db: AsyncSession = Depends(get_db)):
    """Get list of deployed canisters (projects with canister_id)."""
    try:
        # Get projects with canister_id
        result = await db.execute(
            select(Project)
            .where(Project.canister_id.isnot(None))
            .order_by(Project.updated_at.desc())
        )
        projects = result.scalars().all()

        canisters = []
        for project in projects:
            if project.canister_id:
                live_metrics = generate_mock_metrics(project.id, project.canister_id)

                canisters.append(
                    {
                        "id": project.id,
                        "name": project.name,
                        "canister_id": project.canister_id,
                        "status": project.status,
                        "url": f"https://{project.canister_id}.icp0.io/",
                        "cycles_balance": live_metrics["cycles_balance"],
                        "requests_today": live_metrics["requests_today"],
                        "storage_used_bytes": live_metrics["storage_used_bytes"],
                        "is_healthy": live_metrics["is_healthy"],
                        "created_at": project.created_at.isoformat(),
                        "updated_at": project.updated_at.isoformat(),
                    }
                )

        return {
            "success": True,
            "data": canisters,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/dashboard/activities")
async def get_dashboard_activities(db: AsyncSession = Depends(get_db)):
    """Get recent activity log (mock data for now)."""
    try:
        # Get recent projects for activity feed
        result = await db.execute(select(Project).order_by(Project.updated_at.desc()).limit(10))
        projects = result.scalars().all()

        activities = []
        for i, project in enumerate(projects):
            # Generate mock activities
            if project.canister_id:
                activities.append(
                    {
                        "id": f"activity_{project.id}_{i}",
                        "title": f"Deployment completed: {project.name}",
                        "description": f"Project successfully deployed to canister {project.canister_id[:8]}...",
                        "timestamp": project.updated_at.isoformat(),
                        "status": "success",
                        "project_id": project.id,
                    }
                )
            else:
                activities.append(
                    {
                        "id": f"activity_{project.id}_{i}",
                        "title": f"Project created: {project.name}",
                        "description": f"New project '{project.name}' created and ready for deployment",
                        "timestamp": project.created_at.isoformat(),
                        "status": "pending",
                        "project_id": project.id,
                    }
                )

        return {
            "success": True,
            "data": activities,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
