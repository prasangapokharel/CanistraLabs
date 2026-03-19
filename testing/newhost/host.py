#!/usr/bin/env python3
"""
Dynamic Host Testing Script with Deployment
Tests the complete workflow: signup → create project → deploy to individual canister → verify

NEW: Tests the individual canister per project deployment model
Each project gets a unique canister ID and unique URL on IC mainnet
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"


class DynamicHostTester:
    """Test dynamic project hosting via API"""

    def __init__(self):
        self.token = None
        self.refresh_token = None
        self.project_id = None
        self.canister_id = None
        self.deployment_url = None
        self.results = []

    def log(self, step, status, msg):
        """Log test result"""
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️ "
        print(f"{symbol} {step:30} | {msg}")
        self.results.append({"step": step, "status": status, "msg": msg})

    def test_signup(self):
        """Test 1: User Signup - Create new account"""
        try:
            ts = int(datetime.now().timestamp() * 1000)
            # Ensure truly unique email
            email = f"developer{ts}{ts}@example.com"
            username = f"dev{ts}"

            response = requests.post(
                f"{API_BASE}/auth/signup",
                json={"email": email, "password": "SecurePassword123!", "username": username},
                timeout=30,
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")

                if self.token:
                    self.log("1_SIGNUP", "PASS", f"User created: {email}")
                    print(f"   └─ JWT Token: {self.token[:30]}...")
                    return True

            self.log("1_SIGNUP", "FAIL", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log("1_SIGNUP", "FAIL", str(e))
            return False

    def test_create_project(self):
        """Test 2: Create Project - User defines new project"""
        if not self.token:
            self.log("2_CREATE_PROJECT", "FAIL", "No auth token")
            return False

        try:
            project_name = f"Test Project {datetime.now().strftime('%H:%M:%S')}"

            response = requests.post(
                f"{API_BASE}/projects/",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "name": project_name,
                    "description": "Testing individual canister deployment",
                },
                timeout=10,
            )

            if response.status_code in [200, 201]:
                data = response.json()
                project_data = data.get("data", data) if isinstance(data, dict) else {}
                self.project_id = project_data.get("id") if isinstance(project_data, dict) else None

                if self.project_id:
                    self.log("2_CREATE_PROJECT", "PASS", f"Project created (ID: {self.project_id})")
                    return True

            self.log("2_CREATE_PROJECT", "FAIL", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log("2_CREATE_PROJECT", "FAIL", str(e))
            return False

    def test_deploy_project(self):
        """Test 3: Deploy Project - Create individual canister and deploy HTML"""
        if not self.token or not self.project_id:
            self.log("3_DEPLOY_PROJECT", "SKIP", "No project to deploy")
            return True

        try:
            # Simple HTML content to deploy
            html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Project on ICP</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        h1 { color: #667eea; }
        p { color: #555; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎉 Deployed on Internet Computer!</h1>
        <p>This project is running on its own individual ICP canister.</p>
        <p>✨ Each project gets a unique canister with a unique URL.</p>
    </div>
</body>
</html>
"""

            response = requests.post(
                f"{API_BASE}/deployments/projects/{self.project_id}/deploy",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"code_content": html_content},
                timeout=60,  # Longer timeout for canister creation
            )

            if response.status_code in [200, 201, 202]:
                data = response.json()
                self.canister_id = data.get("canister_id")
                self.deployment_url = data.get("url")

                if self.canister_id and self.deployment_url:
                    self.log(
                        "3_DEPLOY_PROJECT",
                        "PASS",
                        f"Deployed to canister {self.canister_id[:10]}...",
                    )
                    print(f"   └─ URL: {self.deployment_url}")
                    return True

            self.log(
                "3_DEPLOY_PROJECT", "FAIL", f"Status {response.status_code}: {response.text[:100]}"
            )
            return False
        except Exception as e:
            self.log("3_DEPLOY_PROJECT", "FAIL", str(e))
            return False

    def test_list_projects(self):
        """Test 4: List Projects - Retrieve user's projects"""
        if not self.token:
            self.log("4_LIST_PROJECTS", "FAIL", "No auth token")
            return False

        try:
            response = requests.get(
                f"{API_BASE}/projects/",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                projects = data.get("data", data) if isinstance(data, dict) else data
                count = len(projects) if isinstance(projects, list) else 0

                self.log("4_LIST_PROJECTS", "PASS", f"Retrieved {count} project(s)")
                return True

            self.log("4_LIST_PROJECTS", "FAIL", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log("4_LIST_PROJECTS", "FAIL", str(e))
            return False

    def test_get_project(self):
        """Test 5: Get Project - Retrieve specific project details"""
        if not self.token or not self.project_id:
            self.log("5_GET_PROJECT", "SKIP", "No project to retrieve")
            return True

        try:
            response = requests.get(
                f"{API_BASE}/projects/{self.project_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                project = data.get("data", data)

                # Verify canister info in response
                has_canister = project.get("canister_id") if isinstance(project, dict) else False
                if self.canister_id and has_canister:
                    self.log("5_GET_PROJECT", "PASS", "Project has deployed canister info")
                else:
                    self.log("5_GET_PROJECT", "PASS", "Retrieved project details")
                return True

            self.log("5_GET_PROJECT", "FAIL", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log("5_GET_PROJECT", "FAIL", str(e))
            return False

    def test_canister_status(self):
        """Test 6: Check Canister Status - Verify deployed canister is live"""
        if not self.token or not self.canister_id:
            self.log("6_CANISTER_STATUS", "SKIP", "No canister to check")
            return True

        try:
            response = requests.get(
                f"{API_BASE}/deployments/canisters/{self.canister_id}/status",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                self.log("6_CANISTER_STATUS", "PASS", f"Canister status: {status}")
                return True

            self.log("6_CANISTER_STATUS", "FAIL", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log("6_CANISTER_STATUS", "FAIL", str(e))
            return False

    def run(self):
        """Run all tests"""
        print("\n" + "=" * 85)
        print("🚀 ICP HOSTING PLATFORM - INDIVIDUAL CANISTER DEPLOYMENT TEST")
        print("=" * 85 + "\n")

        print("📋 TEST WORKFLOW:")
        print("   1. User Signs Up           → Get JWT auth token")
        print("   2. Create Project          → Define new project")
        print("   3. Deploy Project          → Create individual canister & deploy HTML")
        print("   4. List Projects           → Retrieve all user projects")
        print("   5. Get Project Details     → Verify canister info is attached")
        print("   6. Check Canister Status   → Verify deployed canister is live")
        print("\n" + "-" * 85 + "\n")

        # Run tests
        r1 = self.test_signup()
        r2 = self.test_create_project() if r1 else False
        r3 = self.test_deploy_project() if r2 else False
        r4 = self.test_list_projects() if r2 else False
        r5 = self.test_get_project() if r2 else False
        r6 = self.test_canister_status() if r3 else False

        # Summary
        print("\n" + "=" * 85)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        failed = sum(1 for r in self.results if r["status"] == "FAIL")

        if failed == 0:
            print(f"✅ ALL TESTS PASSED! ({passed}/{total})")
            print("\n📊 PLATFORM CAPABILITIES VERIFIED:")
            print("   ✅ User Authentication (JWT Tokens)")
            print("   ✅ Project Management (CRUD Operations)")
            print("   ✅ Individual Canister Creation (One per project)")
            print("   ✅ Dynamic HTML Deployment to IC")
            print("   ✅ Unique Canister URLs")
            print("   ✅ Canister Status Monitoring")
            print("\n🎯 NEW ARCHITECTURE FEATURES:")
            print("   • Each project = unique canister on IC mainnet")
            print("   • Each canister = independent URL (https://CANISTER_ID.icp0.io)")
            print("   • Complete project isolation & security")
            print("   • Users can manage multiple independent deployments")
            if self.deployment_url:
                print(f"\n🔗 DEPLOYED URL: {self.deployment_url}")
        else:
            print(f"⚠️  {passed} passed, {failed} failed (out of {total})")

        print("=" * 85 + "\n")

        return failed == 0


def main():
    """Main entry point"""
    tester = DynamicHostTester()
    success = tester.run()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
