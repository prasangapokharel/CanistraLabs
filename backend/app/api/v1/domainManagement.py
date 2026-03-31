"""
Domain Management API for ICP Hosting Platform.

Provides complete custom domain management including:
- Domain setup and configuration
- DNS verification
- ICP boundary node registration
- SSL certificate management
- Status tracking and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, validator
from typing import Dict, Any, List, Optional, Annotated
import re

from app.database.db import get_db
from app.services.domainManagement import DomainManagementService
from app.services.auth import AuthService
from app.models.domain import CustomDomain
from app.models.project import Project
from app.utils.security import verify_token
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/domains", tags=["Domain Management"])


# Pydantic models for request/response
class DomainSetupRequest(BaseModel):
    """Request model for setting up a custom domain."""

    domain_name: str
    subdomain: Optional[str] = None

    @validator("domain_name")
    def validate_domain_name(cls, v):
        # Basic domain validation
        domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
        if not re.match(domain_pattern, v):
            raise ValueError("Invalid domain name format")
        return v.lower()

    @validator("subdomain")
    def validate_subdomain(cls, v):
        if v:
            # Basic subdomain validation
            subdomain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
            if not re.match(subdomain_pattern, v):
                raise ValueError("Invalid subdomain format")
            return v.lower()
        return v


class DomainStatusResponse(BaseModel):
    """Response model for domain status."""

    success: bool
    domain_id: Optional[int] = None
    domain: Optional[str] = None
    canister_id: Optional[str] = None
    status: Optional[str] = None
    dns_configured: Optional[bool] = None
    ssl_active: Optional[bool] = None
    custom_url: Optional[str] = None
    error: Optional[str] = None


# Authentication dependencies
async def get_bearer_token(authorization: Annotated[Optional[str], Header()] = None) -> str:
    """Extract bearer token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    return parts[1]


async def get_current_user_id(
    authorization: Annotated[str, Depends(get_bearer_token)],
) -> int:
    """Get current user ID from token."""
    token_data = verify_token(authorization, token_type="access")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return int(token_data.sub)


@router.post("/projects/{project_id}/setup")
async def setup_custom_domain(
    project_id: int,
    domain_request: DomainSetupRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Set up a custom domain for a project.

    This endpoint:
    1. Validates project ownership
    2. Creates domain configuration
    3. Generates DNS setup instructions
    4. Returns step-by-step setup guide
    """
    try:
        domain_service = DomainManagementService()

        result = await domain_service.setup_custom_domain(
            session=session,
            project_id=project_id,
            user_id=user_id,
            domain_name=domain_request.domain_name,
            subdomain=domain_request.subdomain,
        )

        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

        return {"success": True, "message": "Domain setup initiated successfully", "data": result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Domain setup failed: {str(e)}",
        )


@router.post("/domains/{domain_id}/verify-dns")
async def verify_domain_dns(
    domain_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Verify DNS configuration for a custom domain.

    Checks all required DNS records:
    - CNAME/ALIAS record pointing to icp1.io
    - TXT record with canister ID
    - ACME challenge CNAME for SSL
    """
    try:
        # Verify user owns this domain
        result = await session.execute(
            select(CustomDomain).where(
                CustomDomain.id == domain_id, CustomDomain.user_id == user_id
            )
        )
        domain = result.scalar_one_or_none()

        if not domain:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

        domain_service = DomainManagementService()
        verification_result = await domain_service.verify_dns_configuration(
            session=session, domain_id=domain_id
        )

        if not verification_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=verification_result["error"]
            )

        return {
            "success": True,
            "message": "DNS verification completed",
            "data": verification_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DNS verification failed: {str(e)}",
        )


@router.post("/domains/{domain_id}/register")
async def register_domain_with_icp(
    domain_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Register domain with ICP boundary nodes for SSL certificate provisioning.

    This step should be done after DNS verification is complete.
    """
    try:
        # Verify user owns this domain
        result = await session.execute(
            select(CustomDomain).where(
                CustomDomain.id == domain_id, CustomDomain.user_id == user_id
            )
        )
        domain = result.scalar_one_or_none()

        if not domain:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

        domain_service = DomainManagementService()
        registration_result = await domain_service.register_with_icp_boundary_nodes(
            session=session, domain_id=domain_id
        )

        if not registration_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=registration_result["error"]
            )

        return {
            "success": True,
            "message": "Domain registration submitted to ICP boundary nodes",
            "data": registration_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Domain registration failed: {str(e)}",
        )


@router.get("/domains/{domain_id}/status")
async def get_domain_status(
    domain_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get complete status of domain configuration and SSL certificate.
    """
    try:
        # Verify user owns this domain
        result = await session.execute(
            select(CustomDomain).where(
                CustomDomain.id == domain_id, CustomDomain.user_id == user_id
            )
        )
        domain = result.scalar_one_or_none()

        if not domain:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

        domain_service = DomainManagementService()
        status_result = await domain_service.get_domain_status(session=session, domain_id=domain_id)

        if not status_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=status_result["error"]
            )

        return {"success": True, "data": status_result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}",
        )


@router.post("/domains/{domain_id}/check-registration")
async def check_domain_registration_status(
    domain_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Check the status of ICP boundary node registration and SSL certificate.
    """
    try:
        # Verify user owns this domain
        result = await session.execute(
            select(CustomDomain).where(
                CustomDomain.id == domain_id, CustomDomain.user_id == user_id
            )
        )
        domain = result.scalar_one_or_none()

        if not domain:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

        domain_service = DomainManagementService()
        check_result = await domain_service.check_registration_status(
            session=session, domain_id=domain_id
        )

        if not check_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=check_result["error"]
            )

        return {"success": True, "message": "Registration status updated", "data": check_result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration status check failed: {str(e)}",
        )


@router.get("/projects/{project_id}/domains")
async def list_project_domains(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    List all custom domains configured for a project.
    """
    try:
        # Verify project ownership
        project_result = await session.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        # Get all domains for this project
        domains_result = await session.execute(
            select(CustomDomain).where(CustomDomain.project_id == project_id)
        )
        domains = domains_result.scalars().all()

        domain_list = []
        for domain in domains:
            domain_list.append(
                {
                    "domain_id": domain.id,
                    "domain": domain.full_domain,
                    "status": domain.status,
                    "dns_configured": domain.dns_configured,
                    "ssl_active": domain.ssl_active,
                    "custom_url": domain.custom_url if domain.status == "active" else None,
                    "canister_url": domain.canister_url,
                    "created_at": domain.created_at.isoformat(),
                    "activated_at": domain.activated_at.isoformat()
                    if domain.activated_at
                    else None,
                }
            )

        return {
            "success": True,
            "project_id": project_id,
            "canister_id": project.canister_id,
            "canister_url": project.url,
            "domains": domain_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list domains: {str(e)}",
        )


@router.get("/user/domains")
async def list_user_domains(
    user_id: int = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all custom domains for the current user across all projects.
    """
    try:
        # Get all domains for this user
        domains_result = await session.execute(
            select(CustomDomain).join(Project).where(CustomDomain.user_id == user_id)
        )
        domains = domains_result.scalars().all()

        domain_list = []
        for domain in domains:
            domain_list.append(
                {
                    "domain_id": domain.id,
                    "project_id": domain.project_id,
                    "domain": domain.full_domain,
                    "status": domain.status,
                    "dns_configured": domain.dns_configured,
                    "ssl_active": domain.ssl_active,
                    "custom_url": domain.custom_url if domain.status == "active" else None,
                    "canister_url": domain.canister_url,
                    "created_at": domain.created_at.isoformat(),
                    "activated_at": domain.activated_at.isoformat()
                    if domain.activated_at
                    else None,
                }
            )

        return {
            "success": True,
            "user_id": user_id,
            "total_domains": len(domain_list),
            "domains": domain_list,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list user domains: {str(e)}",
        )


@router.delete("/domains/{domain_id}")
async def delete_custom_domain(
    domain_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Remove a custom domain configuration.

    Note: This only removes the configuration from our platform.
    Users should also remove DNS records from their registrar.
    """
    try:
        # Verify user owns this domain
        result = await session.execute(
            select(CustomDomain).where(
                CustomDomain.id == domain_id, CustomDomain.user_id == user_id
            )
        )
        domain = result.scalar_one_or_none()

        if not domain:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

        domain_name = domain.full_domain

        # Delete the domain (cascades to verification records)
        await session.delete(domain)
        await session.commit()

        return {
            "success": True,
            "message": f"Domain {domain_name} removed successfully",
            "note": "Please also remove DNS records from your domain registrar",
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete domain: {str(e)}",
        )


# Utility endpoint for DNS instructions
@router.get("/dns-instructions/{canister_id}")
async def get_dns_instructions(canister_id: str, domain: str) -> Dict[str, Any]:
    """
    Get DNS configuration instructions for any domain and canister ID.
    Useful for users setting up domains manually.
    """
    try:
        domain_service = DomainManagementService()
        dns_config = domain_service._generate_dns_config(domain, canister_id)
        ic_domains_content = domain_service._generate_ic_domains_content(domain)

        return {
            "success": True,
            "domain": domain,
            "canister_id": canister_id,
            "dns_configuration": dns_config,
            "ic_domains_file": {"path": ".well-known/ic-domains", "content": ic_domains_content},
            "ic_assets_config": {
                "path": ".ic-assets.json5",
                "content": [{"match": ".well-known", "ignore": False}],
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate DNS instructions: {str(e)}",
        )
