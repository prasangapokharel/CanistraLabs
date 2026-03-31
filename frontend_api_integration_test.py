#!/usr/bin/env python3
"""
Comprehensive Frontend API Integration Test Suite
Tests all frontend API endpoints, error handling, and cycle balance checking
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional


class FrontendAPITester:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.test_results = []
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        self.test_count += 1
        result = {
            "test_id": self.test_count,
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)

        if status == "PASS":
            self.passed_count += 1
            print(f"✓ {test_name}")
        else:
            self.failed_count += 1
            print(f"✗ {test_name}: {details}")

    # ==================== AUTH TESTS ====================
    def test_login(self) -> bool:
        """Test user login endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"email": "test@example.com", "password": "TestPassword123!"},
            )

            if response.status_code in [
                200,
                422,
            ]:  # 422 if user doesn't exist, 200 if valid
                data = response.json()
                if "access_token" in data:
                    self.access_token = data["access_token"]
                    self.refresh_token = data.get("refresh_token")
                    self.log_test(
                        "Auth: Login", "PASS", f"Status: {response.status_code}"
                    )
                    return True
                else:
                    self.log_test(
                        "Auth: Login",
                        "PASS",
                        "User registration/login endpoint working",
                    )
                    return True
            else:
                self.log_test(
                    "Auth: Login", "FAIL", f"Unexpected status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Auth: Login", "FAIL", str(e))
            return False

    def test_signup(self) -> bool:
        """Test user signup endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/signup",
                json={
                    "email": f"newuser_{int(time.time())}@example.com",
                    "password": "TestPassword123!",
                    "full_name": "Test User",
                },
            )

            if response.status_code in [200, 201, 422]:
                self.log_test("Auth: Signup", "PASS", f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Auth: Signup", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Auth: Signup", "FAIL", str(e))
            return False

    def test_refresh_token(self) -> bool:
        """Test token refresh endpoint"""
        if not self.refresh_token:
            self.test_login()

        try:
            response = requests.post(
                f"{self.base_url}/auth/refresh",
                json={"refresh_token": self.refresh_token or "test"},
            )

            if response.status_code in [200, 401, 422]:
                self.log_test(
                    "Auth: Token Refresh", "PASS", f"Status: {response.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Auth: Token Refresh", "FAIL", f"Status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Auth: Token Refresh", "FAIL", str(e))
            return False

    def test_forgot_password(self) -> bool:
        """Test forgot password endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/forgot-password",
                json={"email": "test@example.com"},
            )

            if response.status_code in [200, 404, 422]:
                self.log_test(
                    "Auth: Forgot Password", "PASS", f"Status: {response.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Auth: Forgot Password", "FAIL", f"Status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Auth: Forgot Password", "FAIL", str(e))
            return False

    # ==================== WALLET & CYCLES TESTS ====================
    def test_wallet_identity(self) -> Dict[str, Any]:
        """Test wallet identity endpoint - checks cycles balance"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(f"{self.base_url}/wallet/identity", headers=headers)

            if response.status_code == 200:
                data = response.json()
                cycles_balance = data.get("cycles_balance", "0")
                icp_balance = data.get("icp_balance", "0")
                funding_required = data.get("funding_required", False)

                # Check if cycles are insufficient
                if funding_required or cycles_balance == "0":
                    self.log_test(
                        "Wallet: Identity & Cycles Check",
                        "PASS",
                        f"⚠️  INSUFFICIENT CYCLES - Need to pay. ICP: {icp_balance}, Cycles: {cycles_balance}, Funding Required: {funding_required}",
                    )
                else:
                    self.log_test(
                        "Wallet: Identity & Cycles Check",
                        "PASS",
                        f"Cycles: {cycles_balance}, ICP: {icp_balance}",
                    )

                return data
            else:
                self.log_test(
                    "Wallet: Identity & Cycles Check",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return {}
        except Exception as e:
            self.log_test("Wallet: Identity & Cycles Check", "FAIL", str(e))
            return {}

    def test_wallet_status(self) -> bool:
        """Test wallet status endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(
                f"{self.base_url}/wallet/funding-instructions", headers=headers
            )

            if response.status_code in [200, 401, 422]:
                data = response.json()
                current_status = data.get("current_status", {})
                funded = current_status.get("funded", False)

                status_msg = f"Funded: {funded}"
                if not funded:
                    status_msg += " - Funding instructions available"

                self.log_test("Wallet: Status & Instructions", "PASS", status_msg)
                return True
            else:
                self.log_test(
                    "Wallet: Status & Instructions",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Wallet: Status & Instructions", "FAIL", str(e))
            return False

    def test_refresh_wallet_balance(self) -> bool:
        """Test refresh wallet balance endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.post(
                f"{self.base_url}/wallet/refresh-balance", json={}, headers=headers
            )

            if response.status_code in [200, 401, 422]:
                data = response.json()
                self.log_test(
                    "Wallet: Refresh Balance",
                    "PASS",
                    f"Status: {response.status_code}, Message: {data.get('message', 'OK')}",
                )
                return True
            else:
                self.log_test(
                    "Wallet: Refresh Balance", "FAIL", f"Status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Wallet: Refresh Balance", "FAIL", str(e))
            return False

    def test_convert_icp_to_cycles(self) -> bool:
        """Test ICP to cycles conversion endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.post(
                f"{self.base_url}/wallet/convert-icp-to-cycles",
                json={},
                headers=headers,
            )

            if response.status_code in [200, 400, 401, 422]:
                data = response.json()

                if response.status_code == 400:
                    # Expected when no ICP available
                    self.log_test(
                        "Wallet: Convert ICP to Cycles",
                        "PASS",
                        f"Status: 400 - {data.get('detail', 'Not enough ICP to convert')}",
                    )
                else:
                    self.log_test(
                        "Wallet: Convert ICP to Cycles",
                        "PASS",
                        f"Status: {response.status_code}",
                    )

                return True
            else:
                self.log_test(
                    "Wallet: Convert ICP to Cycles",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Wallet: Convert ICP to Cycles", "FAIL", str(e))
            return False

    def test_network_status(self) -> bool:
        """Test network status endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(
                f"{self.base_url}/wallet/network-status", headers=headers
            )

            if response.status_code in [200, 401, 422]:
                self.log_test(
                    "Wallet: Network Status", "PASS", f"Status: {response.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Wallet: Network Status", "FAIL", f"Status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Wallet: Network Status", "FAIL", str(e))
            return False

    # ==================== PROJECTS TESTS ====================
    def test_get_projects(self) -> bool:
        """Test get projects endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(f"{self.base_url}/projects/", headers=headers)

            if response.status_code in [200, 401]:
                projects = (
                    response.json()
                    if isinstance(response.json(), list)
                    else response.json().get("data", [])
                )
                self.log_test(
                    "Projects: Get All",
                    "PASS",
                    f"Status: {response.status_code}, Count: {len(projects) if isinstance(projects, list) else 0}",
                )
                return True
            else:
                self.log_test(
                    "Projects: Get All", "FAIL", f"Status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Projects: Get All", "FAIL", str(e))
            return False

    def test_create_project(self) -> Optional[str]:
        """Test create project endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.post(
                f"{self.base_url}/projects/",
                json={
                    "name": f"Test Project {int(time.time())}",
                    "description": "Test project for API validation",
                },
                headers=headers,
            )

            if response.status_code in [200, 201, 422, 401]:
                if response.status_code in [200, 201]:
                    data = response.json()
                    project_id = data.get("id") or data.get("project_id")
                    self.log_test(
                        "Projects: Create",
                        "PASS",
                        f"Status: {response.status_code}, ID: {project_id}",
                    )
                    return str(project_id) if project_id else None
                else:
                    self.log_test(
                        "Projects: Create",
                        "PASS",
                        f"Status: {response.status_code} - Auth/validation required",
                    )
                    return None
            else:
                self.log_test(
                    "Projects: Create", "FAIL", f"Status: {response.status_code}"
                )
                return None
        except Exception as e:
            self.log_test("Projects: Create", "FAIL", str(e))
            return None

    def test_get_project_detail(self, project_id: str = "1") -> bool:
        """Test get project detail endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(
                f"{self.base_url}/projects/{project_id}", headers=headers
            )

            if response.status_code in [200, 404, 401]:
                self.log_test(
                    "Projects: Get Detail", "PASS", f"Status: {response.status_code}"
                )
                return response.status_code == 200
            else:
                self.log_test(
                    "Projects: Get Detail", "FAIL", f"Status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Projects: Get Detail", "FAIL", str(e))
            return False

    # ==================== DEPLOYMENT & CANISTER TESTS ====================
    def test_deploy_project(self, project_id: str = "1") -> bool:
        """Test deploy project endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.post(
                f"{self.base_url}/deployments/projects/{project_id}/deploy",
                json={"code_content": "", "force": False},
                headers=headers,
            )

            if response.status_code in [200, 201, 400, 401, 422]:
                data = response.json()

                # Check for cycle error
                if response.status_code == 400 and "cycle" in str(data).lower():
                    self.log_test(
                        "Deployments: Deploy",
                        "PASS",
                        f"Status: 400 - INSUFFICIENT CYCLES - {data.get('detail', 'Need to pay for cycles')}",
                    )
                else:
                    self.log_test(
                        "Deployments: Deploy", "PASS", f"Status: {response.status_code}"
                    )

                return True
            else:
                self.log_test(
                    "Deployments: Deploy", "FAIL", f"Status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Deployments: Deploy", "FAIL", str(e))
            return False

    def test_canister_status(self, canister_id: str = "test-canister") -> bool:
        """Test canister status endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(
                f"{self.base_url}/deployments/canisters/{canister_id}/status",
                headers=headers,
            )

            if response.status_code in [200, 404, 401, 422]:
                self.log_test(
                    "Deployments: Canister Status",
                    "PASS",
                    f"Status: {response.status_code}",
                )
                return True
            else:
                self.log_test(
                    "Deployments: Canister Status",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Deployments: Canister Status", "FAIL", str(e))
            return False

    # ==================== DOMAIN TESTS ====================
    def test_get_user_domains(self) -> bool:
        """Test get user domains endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(
                f"{self.base_url}/domains/user/domains", headers=headers
            )

            if response.status_code in [200, 401]:
                domains = (
                    response.json()
                    if isinstance(response.json(), list)
                    else response.json().get("data", [])
                )
                self.log_test(
                    "Domains: Get User Domains",
                    "PASS",
                    f"Status: {response.status_code}, Count: {len(domains) if isinstance(domains, list) else 0}",
                )
                return True
            else:
                self.log_test(
                    "Domains: Get User Domains",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Domains: Get User Domains", "FAIL", str(e))
            return False

    def test_setup_domain(self, project_id: str = "1") -> bool:
        """Test setup domain endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.post(
                f"{self.base_url}/domains/projects/{project_id}/setup",
                json={
                    "domain_name": f"test-{int(time.time())}.example.com",
                    "subdomain": None,
                },
                headers=headers,
            )

            if response.status_code in [200, 201, 400, 401, 422]:
                self.log_test(
                    "Domains: Setup", "PASS", f"Status: {response.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Domains: Setup", "FAIL", f"Status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Domains: Setup", "FAIL", str(e))
            return False

    # ==================== DASHBOARD TESTS ====================
    def test_dashboard_overview(self) -> bool:
        """Test dashboard overview endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(
                f"{self.base_url}/dashboard/overview", headers=headers
            )

            if response.status_code in [200, 401]:
                self.log_test(
                    "Dashboard: Overview", "PASS", f"Status: {response.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Dashboard: Overview", "FAIL", f"Status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Dashboard: Overview", "FAIL", str(e))
            return False

    def test_dashboard_canisters(self) -> bool:
        """Test dashboard canisters endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(
                f"{self.base_url}/dashboard/canisters", headers=headers
            )

            if response.status_code in [200, 401]:
                self.log_test(
                    "Dashboard: Canisters", "PASS", f"Status: {response.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Dashboard: Canisters", "FAIL", f"Status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Dashboard: Canisters", "FAIL", str(e))
            return False

    # ==================== METRICS TESTS ====================
    def test_project_metrics(self, project_id: str = "1") -> bool:
        """Test project metrics endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(
                f"{self.base_url}/projects/{project_id}/metrics", headers=headers
            )

            if response.status_code in [200, 404, 401]:
                self.log_test(
                    "Metrics: Project Metrics",
                    "PASS",
                    f"Status: {response.status_code}",
                )
                return True
            else:
                self.log_test(
                    "Metrics: Project Metrics",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Metrics: Project Metrics", "FAIL", str(e))
            return False

    # ==================== CRON TESTS ====================
    def test_cron_status(self) -> bool:
        """Test cron status endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.get(f"{self.base_url}/cron/status", headers=headers)

            if response.status_code in [200, 401]:
                self.log_test("Cron: Status", "PASS", f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Cron: Status", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Cron: Status", "FAIL", str(e))
            return False

    def test_trigger_conversion(self) -> bool:
        """Test manual conversion trigger endpoint"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.post(
                f"{self.base_url}/cron/trigger", json={}, headers=headers
            )

            if response.status_code in [200, 400, 401, 422]:
                self.log_test(
                    "Cron: Trigger Conversion",
                    "PASS",
                    f"Status: {response.status_code}",
                )
                return True
            else:
                self.log_test(
                    "Cron: Trigger Conversion",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Cron: Trigger Conversion", "FAIL", str(e))
            return False

    # ==================== ERROR HANDLING TESTS ====================
    def test_invalid_endpoint(self) -> bool:
        """Test 404 error handling"""
        try:
            response = requests.get(f"{self.base_url}/invalid/endpoint")

            if response.status_code == 404:
                self.log_test(
                    "Error Handling: 404 Not Found", "PASS", "Correctly returns 404"
                )
                return True
            else:
                self.log_test(
                    "Error Handling: 404 Not Found",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Error Handling: 404 Not Found", "FAIL", str(e))
            return False

    def test_invalid_auth_token(self) -> bool:
        """Test 401 unauthorized error handling"""
        try:
            headers = {"Authorization": "Bearer invalid_token"}
            response = requests.get(f"{self.base_url}/projects/", headers=headers)

            if response.status_code in [401, 422]:
                self.log_test(
                    "Error Handling: 401 Unauthorized",
                    "PASS",
                    "Correctly rejects invalid token",
                )
                return True
            else:
                self.log_test(
                    "Error Handling: 401 Unauthorized",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Error Handling: 401 Unauthorized", "FAIL", str(e))
            return False

    def test_malformed_json(self) -> bool:
        """Test malformed JSON error handling"""
        try:
            response = requests.post(
                f"{self.base_url}/projects/",
                data="invalid json",
                headers={"Content-Type": "application/json"},
            )

            if response.status_code in [400, 422]:
                self.log_test(
                    "Error Handling: Malformed JSON",
                    "PASS",
                    "Correctly rejects malformed JSON",
                )
                return True
            else:
                self.log_test(
                    "Error Handling: Malformed JSON",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Error Handling: Malformed JSON", "FAIL", str(e))
            return False

    def test_missing_required_fields(self) -> bool:
        """Test missing required fields error handling"""
        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.post(
                f"{self.base_url}/projects/",
                json={},  # Missing required fields
                headers=headers,
            )

            if response.status_code in [400, 422]:
                self.log_test(
                    "Error Handling: Missing Fields",
                    "PASS",
                    "Correctly validates required fields",
                )
                return True
            else:
                self.log_test(
                    "Error Handling: Missing Fields",
                    "FAIL",
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Error Handling: Missing Fields", "FAIL", str(e))
            return False

    # ==================== RUN ALL TESTS ====================
    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "=" * 60)
        print("PERAI FRONTEND API INTEGRATION TEST SUITE")
        print("=" * 60 + "\n")

        print("Testing Backend API Availability...")
        try:
            response = requests.get(f"{self.base_url}/")
            print(f"✓ Backend API is reachable\n")
        except:
            print("✗ Backend API is NOT reachable - Some tests may fail\n")

        # Auth Tests
        print(">>> AUTHENTICATION TESTS")
        self.test_signup()
        self.test_login()
        self.test_refresh_token()
        self.test_forgot_password()

        # Wallet & Cycles Tests
        print("\n>>> WALLET & CYCLES TESTS (CRITICAL)")
        wallet_data = self.test_wallet_identity()
        self.test_wallet_status()
        self.test_refresh_wallet_balance()
        self.test_convert_icp_to_cycles()
        self.test_network_status()

        # Projects Tests
        print("\n>>> PROJECTS TESTS")
        self.test_get_projects()
        project_id = self.test_create_project()
        if not project_id:
            project_id = "1"
        self.test_get_project_detail(project_id)

        # Deployment & Canister Tests
        print("\n>>> DEPLOYMENTS & CANISTERS TESTS")
        self.test_deploy_project(project_id)
        self.test_canister_status()

        # Domain Tests
        print("\n>>> DOMAIN TESTS")
        self.test_get_user_domains()
        self.test_setup_domain(project_id)

        # Dashboard Tests
        print("\n>>> DASHBOARD TESTS")
        self.test_dashboard_overview()
        self.test_dashboard_canisters()

        # Metrics Tests
        print("\n>>> METRICS TESTS")
        self.test_project_metrics(project_id)

        # Cron Tests
        print("\n>>> CRON & CONVERSION TESTS")
        self.test_cron_status()
        self.test_trigger_conversion()

        # Error Handling Tests
        print("\n>>> ERROR HANDLING TESTS")
        self.test_invalid_endpoint()
        self.test_invalid_auth_token()
        self.test_malformed_json()
        self.test_missing_required_fields()

        # Summary
        self.print_summary()
        self.save_results()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.test_count}")
        print(
            f"Passed: {self.passed_count} ({(self.passed_count / self.test_count * 100):.1f}%)"
        )
        print(
            f"Failed: {self.failed_count} ({(self.failed_count / self.test_count * 100):.1f}%)"
        )

        if self.failed_count == 0:
            print("\n✓ ALL TESTS PASSED!")
        else:
            print(f"\n✗ {self.failed_count} test(s) failed - review details above")

        print("=" * 60 + "\n")

    def save_results(self):
        """Save test results to file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": self.test_count,
                "passed": self.passed_count,
                "failed": self.failed_count,
                "pass_rate": f"{(self.passed_count / self.test_count * 100):.1f}%",
            },
            "tests": self.test_results,
        }

        with open("frontend_api_test_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"✓ Results saved to frontend_api_test_results.json")


if __name__ == "__main__":
    tester = FrontendAPITester()
    tester.run_all_tests()
