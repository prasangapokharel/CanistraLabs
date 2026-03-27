#!/usr/bin/env python3
"""
Comprehensive API Endpoint Test Suite

This test suite validates all API endpoints in the ICP Hosting Platform.
It tests authentication, project management, deployments, wallet operations, and more.

Usage:
    python test_api_endpoints.py [--base-url http://localhost:8000] [--email test@example.com] [--password testpass]
"""

import asyncio
import json
import sys
import os
import argparse
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class APITester:
    """Comprehensive API testing client."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        # Use environment variable with fallback to parameter, then default
        default_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
        if base_url and not base_url.endswith("/api/v1"):
            base_url = f"{base_url.rstrip('/')}/api/v1"
        self.base_url = (base_url or default_base_url).rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.current_user: Optional[Dict[str, Any]] = None

        # Test data storage
        self.test_results: List[Dict[str, Any]] = []
        self.created_projects: List[str] = []

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get request headers with optional authentication."""
        headers = {"Content-Type": "application/json"}
        if include_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        include_auth: bool = True,
        expected_status: int = 200,
    ) -> Dict[str, Any]:
        """Make HTTP request and return response data."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(include_auth)

        try:
            async with self.session.request(
                method, url, json=data, headers=headers
            ) as response:
                response_text = await response.text()

                # Try to parse JSON, fall back to text
                try:
                    response_data = await response.json() if response_text else {}
                except:
                    response_data = {"text": response_text}

                result = {
                    "status": response.status,
                    "data": response_data,
                    "headers": dict(response.headers),
                    "success": response.status == expected_status,
                }

                if not result["success"]:
                    logger.warning(
                        f"{method} {endpoint} - Expected {expected_status}, got {response.status}: {response_data}"
                    )

                return result

        except Exception as e:
            logger.error(f"Request failed: {method} {endpoint} - {str(e)}")
            return {
                "status": 0,
                "data": {"error": str(e)},
                "headers": {},
                "success": False,
            }

    def _record_test(
        self,
        test_name: str,
        success: bool,
        details: str,
        response: Optional[Dict] = None,
    ):
        """Record test result."""
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "details": details,
                "timestamp": datetime.now().isoformat(),
                "status_code": response.get("status") if response else None,
                "response_data": response.get("data") if response else None,
            }
        )

        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {details}")

    # Authentication Tests

    async def test_signup(
        self, email: str, password: str, username: str = None
    ) -> bool:
        """Test user signup."""
        if not username:
            username = email.split("@")[0]

        signup_data = {
            "email": email,
            "password": password,
            "username": username,
            "full_name": f"Test User {username}",
        }

        response = await self._request(
            "POST", "/auth/signup", signup_data, include_auth=False, expected_status=201
        )

        if response["success"]:
            self.access_token = response["data"].get("access_token")
            self.refresh_token = response["data"].get("refresh_token")
            self._record_test(
                "User Signup",
                True,
                f"Successfully created account for {email}",
                response,
            )
            return True
        else:
            self._record_test(
                "User Signup",
                False,
                f"Failed to create account: {response['data']}",
                response,
            )
            return False

    async def test_login(self, email: str, password: str) -> bool:
        """Test user login."""
        login_data = {"email": email, "password": password}

        response = await self._request(
            "POST", "/auth/login", login_data, include_auth=False
        )

        if response["success"]:
            self.access_token = response["data"].get("access_token")
            self.refresh_token = response["data"].get("refresh_token")
            self._record_test(
                "User Login", True, f"Successfully logged in as {email}", response
            )
            return True
        else:
            self._record_test(
                "User Login", False, f"Failed to login: {response['data']}", response
            )
            return False

    async def test_get_current_user(self) -> bool:
        """Test getting current user info."""
        response = await self._request("GET", "/auth/me")

        if response["success"]:
            self.current_user = response["data"]
            self._record_test(
                "Get Current User",
                True,
                f"Retrieved user: {self.current_user.get('email')}",
                response,
            )
            return True
        else:
            self._record_test(
                "Get Current User",
                False,
                f"Failed to get user info: {response['data']}",
                response,
            )
            return False

    async def test_refresh_token(self) -> bool:
        """Test token refresh."""
        if not self.refresh_token:
            self._record_test("Token Refresh", False, "No refresh token available")
            return False

        refresh_data = {"refresh_token": self.refresh_token}
        response = await self._request(
            "POST", "/auth/refresh", refresh_data, include_auth=False
        )

        if response["success"]:
            self.access_token = response["data"].get("access_token")
            self.refresh_token = response["data"].get("refresh_token")
            self._record_test(
                "Token Refresh", True, "Successfully refreshed tokens", response
            )
            return True
        else:
            self._record_test(
                "Token Refresh",
                False,
                f"Failed to refresh token: {response['data']}",
                response,
            )
            return False

    async def test_logout(self) -> bool:
        """Test user logout."""
        response = await self._request("POST", "/auth/logout")

        if response["success"]:
            # Clear tokens after successful logout
            self.access_token = None
            self.refresh_token = None
            self._record_test("User Logout", True, "Successfully logged out", response)
            return True
        else:
            self._record_test(
                "User Logout", False, f"Failed to logout: {response['data']}", response
            )
            return False

    # Password Reset Tests

    async def test_forgot_password(self, email: str) -> bool:
        """Test forgot password request."""
        forgot_data = {"email": email}
        response = await self._request(
            "POST", "/auth/forgot-password", forgot_data, include_auth=False
        )

        if response["success"]:
            self._record_test(
                "Forgot Password", True, "Password reset email requested", response
            )
            return True
        else:
            self._record_test(
                "Forgot Password",
                False,
                f"Failed to request password reset: {response['data']}",
                response,
            )
            return False

    async def test_verify_reset_token(self, token: str = "invalid_token") -> bool:
        """Test reset token verification (with invalid token for testing)."""
        response = await self._request(
            "GET",
            f"/auth/verify-reset-token?token={token}",
            include_auth=False,
            expected_status=400,
        )

        # We expect this to fail with an invalid token
        if response["status"] == 400:
            self._record_test(
                "Verify Reset Token", True, "Correctly rejected invalid token", response
            )
            return True
        else:
            self._record_test(
                "Verify Reset Token",
                False,
                f"Unexpected response: {response['data']}",
                response,
            )
            return False

    # Project Management Tests

    async def test_create_project(self, name: str = None) -> Optional[str]:
        """Test project creation."""
        if not name:
            name = f"test-project-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        project_data = {
            "name": name,
            "description": f"Test project created at {datetime.now()}",
            "type": "motoko",
        }

        response = await self._request(
            "POST", "/projects/", project_data, expected_status=201
        )

        if response["success"]:
            project_id = response["data"].get("id")
            if project_id:
                self.created_projects.append(str(project_id))
            self._record_test(
                "Create Project",
                True,
                f"Created project: {name} (ID: {project_id})",
                response,
            )
            return str(project_id) if project_id else None
        else:
            self._record_test(
                "Create Project",
                False,
                f"Failed to create project: {response['data']}",
                response,
            )
            return None

    async def test_get_projects(self) -> bool:
        """Test getting projects list."""
        response = await self._request("GET", "/projects/")

        if response["success"]:
            projects = response["data"]
            project_count = len(projects) if isinstance(projects, list) else 0
            self._record_test(
                "Get Projects", True, f"Retrieved {project_count} projects", response
            )
            return True
        else:
            self._record_test(
                "Get Projects",
                False,
                f"Failed to get projects: {response['data']}",
                response,
            )
            return False

    async def test_get_project_details(self, project_id: str) -> bool:
        """Test getting project details."""
        response = await self._request("GET", f"/projects/{project_id}")

        if response["success"]:
            project = response["data"]
            self._record_test(
                "Get Project Details",
                True,
                f"Retrieved project: {project.get('name')}",
                response,
            )
            return True
        else:
            self._record_test(
                "Get Project Details",
                False,
                f"Failed to get project details: {response['data']}",
                response,
            )
            return False

    async def test_update_project(self, project_id: str) -> bool:
        """Test updating project."""
        update_data = {"description": f"Updated test project at {datetime.now()}"}

        response = await self._request("PUT", f"/projects/{project_id}", update_data)

        if response["success"]:
            self._record_test(
                "Update Project", True, f"Updated project {project_id}", response
            )
            return True
        else:
            self._record_test(
                "Update Project",
                False,
                f"Failed to update project: {response['data']}",
                response,
            )
            return False

    # Wallet Tests

    async def test_get_wallet_identity(self) -> bool:
        """Test getting wallet identity."""
        response = await self._request("GET", "/wallet/identity")

        if response["success"]:
            identity = response["data"]
            principal_id = identity.get("principal_id", "N/A")
            self._record_test(
                "Get Wallet Identity",
                True,
                f"Retrieved identity: {principal_id}",
                response,
            )
            return True
        else:
            self._record_test(
                "Get Wallet Identity",
                False,
                f"Failed to get wallet identity: {response['data']}",
                response,
            )
            return False

    async def test_get_wallet_status(self) -> bool:
        """Test getting wallet funding status."""
        response = await self._request("GET", "/wallet/funding-instructions")

        if response["success"]:
            status = response["data"]
            funded = status.get("current_status", {}).get("funded", False)
            self._record_test(
                "Get Wallet Status", True, f"Wallet funded: {funded}", response
            )
            return True
        else:
            self._record_test(
                "Get Wallet Status",
                False,
                f"Failed to get wallet status: {response['data']}",
                response,
            )
            return False

    async def test_refresh_wallet_balance(self) -> bool:
        """Test refreshing wallet balance."""
        response = await self._request("POST", "/wallet/refresh-balance", {})

        if response["success"]:
            self._record_test(
                "Refresh Wallet Balance",
                True,
                "Balance refreshed successfully",
                response,
            )
            return True
        else:
            self._record_test(
                "Refresh Wallet Balance",
                False,
                f"Failed to refresh balance: {response['data']}",
                response,
            )
            return False

    # Deployment Tests

    async def test_deploy_project(self, project_id: str) -> bool:
        """Test project deployment."""
        deploy_data = {"code_content": "", "force": False}

        response = await self._request(
            "POST",
            f"/deployments/projects/{project_id}/deploy",
            deploy_data,
            expected_status=201,
        )

        if response["success"]:
            deployment = response["data"]
            canister_id = deployment.get("canister_id", "N/A")
            self._record_test(
                "Deploy Project", True, f"Deployed to canister: {canister_id}", response
            )
            return True
        else:
            self._record_test(
                "Deploy Project",
                False,
                f"Failed to deploy project: {response['data']}",
                response,
            )
            return False

    # Cleanup Tests

    async def test_delete_project(self, project_id: str) -> bool:
        """Test project deletion."""
        response = await self._request(
            "DELETE", f"/projects/{project_id}", expected_status=204
        )

        if response["success"] or response["status"] == 204:
            self._record_test(
                "Delete Project", True, f"Deleted project {project_id}", response
            )
            return True
        else:
            self._record_test(
                "Delete Project",
                False,
                f"Failed to delete project: {response['data']}",
                response,
            )
            return False

    # Test Runner

    async def run_comprehensive_tests(
        self, email: str, password: str
    ) -> Dict[str, Any]:
        """Run the complete test suite."""
        logger.info(f"Starting comprehensive API tests for {self.base_url}")
        logger.info(f"Testing with credentials: {email}")

        start_time = datetime.now()

        # Authentication Flow
        logger.info("\n🔐 Testing Authentication...")

        # Try login first (user might already exist)
        login_success = await self.test_login(email, password)

        if not login_success:
            # If login fails, try signup
            logger.info("Login failed, attempting signup...")
            signup_success = await self.test_signup(email, password)
            if not signup_success:
                logger.error("Both login and signup failed. Stopping tests.")
                return self._generate_report(start_time, success=False)

        # Get user info
        await self.test_get_current_user()

        # Test token refresh
        await self.test_refresh_token()

        # Password reset flow
        logger.info("\n📧 Testing Password Reset...")
        await self.test_forgot_password(email)
        await self.test_verify_reset_token()

        # Project Management
        logger.info("\n📁 Testing Project Management...")
        await self.test_get_projects()

        project_id = await self.test_create_project()
        if project_id:
            await self.test_get_project_details(project_id)
            await self.test_update_project(project_id)

            # Wallet Tests
            logger.info("\n💰 Testing Wallet Operations...")
            await self.test_get_wallet_identity()
            await self.test_get_wallet_status()
            await self.test_refresh_wallet_balance()

            # Deployment Tests
            logger.info("\n🚀 Testing Deployment...")
            await self.test_deploy_project(project_id)

            # Cleanup
            logger.info("\n🧹 Cleaning up...")
            await self.test_delete_project(project_id)

        # Logout
        logger.info("\n👋 Testing Logout...")
        await self.test_logout()

        return self._generate_report(start_time, success=True)

    def _generate_report(
        self, start_time: datetime, success: bool = True
    ) -> Dict[str, Any]:
        """Generate test report."""
        end_time = datetime.now()
        duration = end_time - start_time

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100)
                if total_tests > 0
                else 0,
                "duration": str(duration),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            "results": self.test_results,
            "base_url": self.base_url,
        }

        return report


async def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Comprehensive API Endpoint Test Suite"
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("API_BASE_URL", "http://localhost:8000"),
        help="API base URL (can also use API_BASE_URL environment variable)",
    )
    parser.add_argument(
        "--email",
        default=os.getenv("TEST_EMAIL", "test@example.com"),
        help="Test email (can also use TEST_EMAIL environment variable)",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("TEST_PASSWORD", "TestPassword123!"),
        help="Test password (can also use TEST_PASSWORD environment variable)",
    )
    parser.add_argument("--output", help="Output file for test results (JSON)")

    args = parser.parse_args()

    async with APITester(args.base_url) as tester:
        report = await tester.run_comprehensive_tests(args.email, args.password)

        # Print summary
        summary = report["summary"]
        print(f"\n" + "=" * 60)
        print(f"TEST SUMMARY")
        print(f"=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Duration: {summary['duration']}")
        print(f"=" * 60)

        # Show failed tests
        failed_tests = [r for r in report["results"] if not r["success"]]
        if failed_tests:
            print(f"\nFAILED TESTS:")
            for test in failed_tests:
                print(f"❌ {test['test']}: {test['details']}")

        # Save report if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nDetailed report saved to: {args.output}")

        # Exit with error code if tests failed
        if summary["failed"] > 0:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
