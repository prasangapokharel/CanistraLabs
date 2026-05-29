"""
Domain Management Service for ICP Hosting Platform.

Handles custom domain configuration, DNS verification, and SSL certificate management.
Provides complete automation for domain setup and ICP boundary node registration.
"""

import json
import httpx
import dns.resolver
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.domain import (
    CustomDomain,
    DomainVerification,
    DomainStatus,
    DomainRegistrationStatus,
)
from app.models.project import Project
from app.services.dfxCommand import DfxCommand


class DomainManagementService:
    """Service for managing custom domains on ICP."""

    def __init__(self, network: str = "ic"):
        self.network = network
        self.dfx = DfxCommand(network=network)
        self.icp_boundary_node = "https://icp0.io"
        self.icp_api_host = "https://icp-api.io"

    async def setup_custom_domain(
        self,
        session: AsyncSession,
        project_id: int,
        user_id: int,
        domain_name: str,
        subdomain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete custom domain setup process.

        Returns domain configuration with DNS instructions.
        """
        try:
            # Get project and verify ownership
            result = await session.execute(
                select(Project).where(Project.id == project_id, Project.user_id == user_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                return {"success": False, "error": "Project not found"}

            if not project.canister_id:
                return {
                    "success": False,
                    "error": "Project must be deployed before adding custom domain",
                }

            # Check if domain already exists for this project/user/domain tuple
            existing = await session.execute(
                select(CustomDomain).where(
                    CustomDomain.project_id == project_id,
                    CustomDomain.user_id == user_id,
                    CustomDomain.domain_name == domain_name,
                    CustomDomain.subdomain == subdomain,
                )
            )
            if existing.scalar_one_or_none():
                return {"success": False, "error": "Domain already configured"}

            # Create domain record
            full_domain = f"{subdomain}.{domain_name}" if subdomain else domain_name

            custom_domain = CustomDomain(
                project_id=project_id,
                user_id=user_id,
                domain_name=domain_name,
                subdomain=subdomain,
                canister_id=project.canister_id,
                status=DomainStatus.PENDING,
            )

            # Generate DNS instructions
            dns_config = self._generate_dns_config(full_domain, project.canister_id)
            custom_domain.dns_instructions = json.dumps(dns_config)

            # Generate ic-domains content
            ic_domains_content = self._generate_ic_domains_content(full_domain)
            custom_domain.ic_domains_content = ic_domains_content

            session.add(custom_domain)
            await session.flush()

            # Create DNS verification records
            verification_records = [
                DomainVerification(
                    domain_id=custom_domain.id,
                    record_type="CNAME",
                    record_name=full_domain,
                    record_value=f"{full_domain}.icp1.io",
                ),
                DomainVerification(
                    domain_id=custom_domain.id,
                    record_type="TXT",
                    record_name=f"_canister-id.{full_domain}",
                    record_value=project.canister_id,
                ),
                DomainVerification(
                    domain_id=custom_domain.id,
                    record_type="CNAME",
                    record_name=f"_acme-challenge.{full_domain}",
                    record_value=f"_acme-challenge.{full_domain}.icp2.io",
                ),
            ]

            for record in verification_records:
                session.add(record)

            await session.commit()

            return {
                "success": True,
                "domain_id": custom_domain.id,
                "domain": full_domain,
                "canister_id": project.canister_id,
                "status": custom_domain.status,
                "dns_config": dns_config,
                "ic_domains_content": ic_domains_content,
                "next_steps": [
                    "Configure DNS records at your domain registrar",
                    "Deploy .well-known/ic-domains file to your canister",
                    "Verify DNS configuration",
                    "Register with ICP boundary nodes",
                ],
            }

        except Exception as e:
            await session.rollback()
            return {"success": False, "error": f"Domain setup failed: {str(e)}"}

    def _generate_dns_config(self, domain: str, canister_id: str) -> Dict[str, Any]:
        """Generate DNS configuration instructions."""
        return {
            "domain": domain,
            "canister_id": canister_id,
            "records": [
                {
                    "type": "CNAME",
                    "host": domain,
                    "value": f"{domain}.icp1.io",
                    "description": "Points your domain to ICP gateway routing",
                },
                {
                    "type": "TXT",
                    "host": f"_canister-id.{domain}",
                    "value": canister_id,
                    "description": "Associates your domain with your canister",
                },
                {
                    "type": "CNAME",
                    "host": f"_acme-challenge.{domain}",
                    "value": f"_acme-challenge.{domain}.icp2.io",
                    "description": "Enables automatic SSL certificate provisioning",
                },
            ],
            "alternative_records": [
                {
                    "type": "ALIAS/ANAME",
                    "host": domain,
                    "value": f"{domain}.icp1.io",
                    "description": "Use if your registrar doesn't support CNAME on apex domain",
                }
            ],
        }

    def _generate_ic_domains_content(self, domain: str) -> str:
        """Generate content for .well-known/ic-domains file."""
        return domain

    async def verify_dns_configuration(
        self, session: AsyncSession, domain_id: int
    ) -> Dict[str, Any]:
        """Verify DNS records are correctly configured."""
        try:
            # Get domain
            result = await session.execute(select(CustomDomain).where(CustomDomain.id == domain_id))
            domain = result.scalar_one_or_none()

            if not domain:
                return {"success": False, "error": "Domain not found"}

            # Get verification records
            verifications = await session.execute(
                select(DomainVerification).where(DomainVerification.domain_id == domain_id)
            )
            records = verifications.scalars().all()

            verification_results = []
            all_verified = True

            for record in records:
                try:
                    verified = await self._verify_dns_record(
                        record.record_type, record.record_name, record.record_value
                    )

                    record.verified = verified
                    record.last_checked = datetime.utcnow()

                    if verified and not record.verified_at:
                        record.verified_at = datetime.utcnow()

                    if not verified:
                        all_verified = False

                    verification_results.append(
                        {
                            "type": record.record_type,
                            "name": record.record_name,
                            "expected_value": record.record_value,
                            "verified": verified,
                        }
                    )

                except Exception as e:
                    record.error_message = str(e)
                    all_verified = False
                    verification_results.append(
                        {
                            "type": record.record_type,
                            "name": record.record_name,
                            "expected_value": record.record_value,
                            "verified": False,
                            "error": str(e),
                        }
                    )

            # Update domain status
            if all_verified:
                domain.status = DomainStatus.DNS_CONFIGURED
                domain.dns_configured = True
            else:
                domain.status = DomainStatus.PENDING

            await session.commit()

            return {
                "success": True,
                "domain_id": domain_id,
                "domain": domain.full_domain,
                "all_verified": all_verified,
                "verification_results": verification_results,
                "status": domain.status,
                "ready_for_registration": all_verified,
            }

        except Exception as e:
            return {"success": False, "error": f"DNS verification failed: {str(e)}"}

    async def _verify_dns_record(self, record_type: str, name: str, expected_value: str) -> bool:
        """Verify a single DNS record."""
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 10

            if record_type == "CNAME":
                answers = resolver.resolve(name, "CNAME")
                for answer in answers:
                    if str(answer.target).rstrip(".") == expected_value.rstrip("."):
                        return True

            elif record_type == "TXT":
                answers = resolver.resolve(name, "TXT")
                for answer in answers:
                    txt_value = "".join([part.decode() for part in answer.strings])
                    if txt_value == expected_value:
                        return True

            elif record_type == "ALIAS" or record_type == "ANAME":
                # For ALIAS/ANAME, check if domain resolves to ICP boundary node IPs
                answers = resolver.resolve(name, "A")
                # This is a simplified check - in practice you'd verify against known ICP IPs
                return len(answers) > 0

            return False

        except Exception:
            return False

    async def register_with_icp_boundary_nodes(
        self, session: AsyncSession, domain_id: int
    ) -> Dict[str, Any]:
        """Register domain with ICP boundary nodes for SSL certificate provisioning."""
        try:
            # Get domain
            result = await session.execute(select(CustomDomain).where(CustomDomain.id == domain_id))
            domain = result.scalar_one_or_none()

            if not domain:
                return {"success": False, "error": "Domain not found"}

            if domain.status != DomainStatus.DNS_CONFIGURED:
                return {"success": False, "error": "DNS must be configured before registration"}

            # Register with ICP boundary nodes
            async with httpx.AsyncClient(timeout=30) as client:
                registration_data = {"name": domain.full_domain}

                response = await client.post(
                    f"{self.icp_boundary_node}/registrations",
                    json=registration_data,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    result_data = response.json()
                    request_id = result_data.get("id")

                    domain.icp_request_id = request_id
                    domain.status = DomainStatus.REGISTERING
                    domain.registration_status = DomainRegistrationStatus.PROCESSING

                    await session.commit()

                    return {
                        "success": True,
                        "domain_id": domain_id,
                        "domain": domain.full_domain,
                        "request_id": request_id,
                        "status": "registering",
                        "message": "Registration submitted to ICP boundary nodes",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Registration failed: HTTP {response.status_code}",
                        "details": response.text,
                    }

        except Exception as e:
            return {"success": False, "error": f"Registration failed: {str(e)}"}

    async def check_registration_status(
        self, session: AsyncSession, domain_id: int
    ) -> Dict[str, Any]:
        """Check the status of ICP boundary node registration."""
        try:
            # Get domain
            result = await session.execute(select(CustomDomain).where(CustomDomain.id == domain_id))
            domain = result.scalar_one_or_none()

            if not domain or not domain.icp_request_id:
                return {"success": False, "error": "No registration request found"}

            # Check status with ICP boundary nodes
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.icp_boundary_node}/registrations/{domain.icp_request_id}"
                )

                if response.status_code == 200:
                    result_data = response.json()
                    status = result_data.get("state", "Unknown")

                    domain.registration_status = status

                    if status == DomainRegistrationStatus.AVAILABLE.value:
                        domain.status = DomainStatus.ACTIVE
                        domain.ssl_active = True
                        domain.ssl_issued_at = datetime.utcnow()
                        domain.ssl_expires_at = datetime.utcnow() + timedelta(
                            days=90
                        )  # Let's Encrypt default
                        if not domain.activated_at:
                            domain.activated_at = datetime.utcnow()

                    elif status == DomainRegistrationStatus.FAILED.value:
                        domain.status = DomainStatus.FAILED

                    await session.commit()

                    return {
                        "success": True,
                        "domain_id": domain_id,
                        "domain": domain.full_domain,
                        "registration_status": status,
                        "domain_status": domain.status,
                        "ssl_active": domain.ssl_active,
                        "custom_url": domain.custom_url
                        if domain.status == DomainStatus.ACTIVE
                        else None,
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Status check failed: HTTP {response.status_code}",
                    }

        except Exception as e:
            return {"success": False, "error": f"Status check failed: {str(e)}"}

    async def deploy_ic_domains_file(
        self, session: AsyncSession, domain_id: int, identity: str
    ) -> Dict[str, Any]:
        """Deploy .well-known/ic-domains file to canister."""
        try:
            # Get domain
            result = await session.execute(select(CustomDomain).where(CustomDomain.id == domain_id))
            domain = result.scalar_one_or_none()

            if not domain:
                return {"success": False, "error": "Domain not found"}

            # This would integrate with your deployment system to update the canister
            # For now, return instructions for manual deployment

            return {
                "success": True,
                "domain_id": domain_id,
                "instructions": {
                    "file_path": ".well-known/ic-domains",
                    "content": domain.ic_domains_content,
                    "deployment_note": "Add this file to your project and redeploy to update the canister",
                },
                "auto_deployment": "Available in next release",
            }

        except Exception as e:
            return {"success": False, "error": f"File deployment failed: {str(e)}"}

    async def get_domain_status(self, session: AsyncSession, domain_id: int) -> Dict[str, Any]:
        """Get complete domain configuration status."""
        try:
            result = await session.execute(select(CustomDomain).where(CustomDomain.id == domain_id))
            domain = result.scalar_one_or_none()

            if not domain:
                return {"success": False, "error": "Domain not found"}

            # Get verification records
            verifications = await session.execute(
                select(DomainVerification).where(DomainVerification.domain_id == domain_id)
            )
            records = verifications.scalars().all()

            return {
                "success": True,
                "domain_id": domain_id,
                "domain": domain.full_domain,
                "canister_id": domain.canister_id,
                "status": domain.status,
                "registration_status": domain.registration_status,
                "dns_configured": domain.dns_configured,
                "ssl_active": domain.ssl_active,
                "ssl_expires_at": domain.ssl_expires_at.isoformat()
                if domain.ssl_expires_at
                else None,
                "canister_url": domain.canister_url,
                "custom_url": domain.custom_url if domain.status == DomainStatus.ACTIVE else None,
                "verification_records": [
                    {
                        "type": record.record_type,
                        "name": record.record_name,
                        "value": record.record_value,
                        "verified": record.verified,
                        "last_checked": record.last_checked.isoformat()
                        if record.last_checked
                        else None,
                    }
                    for record in records
                ],
                "created_at": domain.created_at.isoformat(),
                "activated_at": domain.activated_at.isoformat() if domain.activated_at else None,
            }

        except Exception as e:
            return {"success": False, "error": f"Status check failed: {str(e)}"}
