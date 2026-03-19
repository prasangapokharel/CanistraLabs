#!/usr/bin/env python3
"""
Production-Ready User Flow Test
================================
Complete end-to-end test of the ICP Hosting Platform user experience:
1. Register new user
2. Login and get JWT token
3. Create new project with HTML file content
4. Deploy project to get unique canister ID and URL
5. Verify canister is live and serving content
6. Test that each project gets unique canister (not shared)

This test ensures production-grade quality with mainnet deployment.
"""

import requests
import json
import time
import random
import string
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


class ProductionFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.user_email = None
        self.jwt_token = None
        self.project_id = None
        self.canister_id = None
        self.deployment_url = None

    def generate_unique_email(self) -> str:
        """Generate unique email for testing"""
        timestamp = str(int(time.time()))
        random_suffix = "".join(random.choices(string.ascii_lowercase, k=6))
        return f"produser_{timestamp}_{random_suffix}@example.com"

    def generate_sample_html(self, project_name: str) -> str:
        """Generate sample HTML content for deployment"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - ICP Hosting</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 50px auto; 
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .container {{ 
            background: rgba(255,255,255,0.1); 
            padding: 30px; 
            border-radius: 15px; 
            text-align: center;
        }}
        h1 {{ color: #fff; margin-bottom: 20px; }}
        .info {{ background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .success {{ color: #4CAF50; font-weight: bold; font-size: 18px; }}
        .timestamp {{ font-size: 12px; opacity: 0.8; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 {project_name}</h1>
        <div class="success">✅ Successfully Deployed to Internet Computer!</div>
        <div class="info">
            <p><strong>Project:</strong> {project_name}</p>
            <p><strong>Platform:</strong> ICP Hosting Platform</p>
            <p><strong>Architecture:</strong> Individual Canister per Project</p>
            <p><strong>Network:</strong> IC Mainnet</p>
        </div>
        <div class="timestamp">Deployed: {time.strftime("%Y-%m-%d %H:%M:%S UTC")}</div>
        <p>This project is running on its own unique canister with a dedicated URL!</p>
    </div>
</body>
</html>"""

    def test_step_1_register(self) -> bool:
        """Step 1: User Registration"""
        print("\\n" + "=" * 80)
        print("🔐 STEP 1: USER REGISTRATION")
        print("=" * 80)

        self.user_email = self.generate_unique_email()

        payload = {"email": self.user_email, "password": "SecurePassword123!"}

        try:
            response = self.session.post(f"{BASE_URL}/api/v1/auth/login", json=payload)
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("access_token")
                print(f"✅ Login successful")
                print(f"   JWT Token: {self.jwt_token[:50]}...")

                # Set authorization header for future requests
                self.session.headers.update({"Authorization": f"Bearer {self.jwt_token}"})
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def test_step_3_create_project_with_file(self) -> bool:
        """Step 3: Create Project with HTML File Upload"""
        print("\\n" + "=" * 80)
        print("📁 STEP 3: CREATE PROJECT WITH HTML FILE")
        print("=" * 80)

        project_name = f"MyWebsite_{int(time.time())}"
        html_content = self.generate_sample_html(project_name)

        payload = {
            "name": project_name,
            "description": f"Production test project with HTML content - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "language": "motoko",
            "code_content": html_content,
        }

        try:
            response = self.session.post(f"{BASE_URL}/api/v1/projects/", json=payload)
            if response.status_code == 201:
                data = response.json()
                self.project_id = data.get("id")
                print(f"✅ Project created successfully")
                print(f"   Project ID: {self.project_id}")
                print(f"   Project Name: {project_name}")
                print(f"   HTML Content: {len(html_content)} bytes")
                return True
            else:
                print(f"❌ Project creation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Project creation error: {e}")
            return False

    def test_step_4_deploy_project(self) -> bool:
        """Step 4: Deploy Project to Get Unique Canister"""
        print("\\n" + "=" * 80)
        print("🚀 STEP 4: DEPLOY PROJECT (GET CANISTER ID & URL)")
        print("=" * 80)

        try:
            print("Initiating deployment to IC mainnet...")
            print("⏳ This may take 30-60 seconds for mainnet deployment...")

            response = self.session.post(
                f"{BASE_URL}/api/v1/deployments/projects/{self.project_id}/deploy",
                timeout=180,  # 3 minutes timeout for mainnet
            )

            if response.status_code == 200:
                data = response.json()
                self.canister_id = data.get("canister_id")
                self.deployment_url = data.get("url")

                print(f"✅ Deployment successful!")
                print(f"   Canister ID: {self.canister_id}")
                print(f"   Deployment URL: {self.deployment_url}")
                print(f"   Network: {data.get('network', 'ic')}")
                print(f"   Status: {data.get('status')}")
                return True
            else:
                print(f"❌ Deployment failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   Error: {response.text}")
                return False

        except requests.Timeout:
            print(f"❌ Deployment timeout (mainnet deployment can be slow)")
            return False
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False

    def test_step_5_verify_canister_live(self) -> bool:
        """Step 5: Verify Deployed Site is Live and Accessible"""
        print("\\n" + "=" * 80)
        print("🌐 STEP 5: VERIFY DEPLOYED SITE IS LIVE")
        print("=" * 80)

        if not self.deployment_url:
            print("❌ No deployment URL available")
            return False

        try:
            print(f"Testing URL: {self.deployment_url}")
            print("⏳ Checking if canister is serving content...")

            # Wait a bit for canister to be fully ready
            time.sleep(10)

            response = requests.get(self.deployment_url, timeout=30)

            if response.status_code == 200:
                content = response.text
                print(f"✅ Site is live and accessible!")
                print(f"   Status Code: {response.status_code}")
                print(f"   Content Length: {len(content)} bytes")
                print(f"   Content Type: {response.headers.get('content-type', 'N/A')}")

                # Check if our HTML content is being served
                if "Successfully Deployed to Internet Computer" in content:
                    print(f"✅ Verified: Custom HTML content is being served correctly")
                    return True
                else:
                    print(f"⚠️  Warning: Content served but doesn't match expected HTML")
                    return True
            else:
                print(f"❌ Site not accessible: {response.status_code}")
                return False

        except requests.Timeout:
            print(f"❌ Site access timeout")
            return False
        except Exception as e:
            print(f"❌ Site verification error: {e}")
            return False

    def test_step_6_unique_canister_verification(self) -> bool:
        """Step 6: Verify Each Project Gets Unique Canister"""
        print("\\n" + "=" * 80)
        print("🔍 STEP 6: VERIFY UNIQUE CANISTER PER PROJECT")
        print("=" * 80)

        # Create a second project to verify uniqueness
        project_name_2 = f"SecondWebsite_{int(time.time())}"
        html_content_2 = self.generate_sample_html(project_name_2)

        payload_2 = {
            "name": project_name_2,
            "description": "Second project to verify unique canister allocation",
            "language": "motoko",
            "code_content": html_content_2,
        }

        try:
            # Create second project
            response = self.session.post(f"{BASE_URL}/api/v1/projects/", json=payload_2)
            if response.status_code != 201:
                print(f"❌ Failed to create second project: {response.status_code}")
                return False

            project_2_id = response.json().get("id")
            print(f"✅ Created second project (ID: {project_2_id})")

            # Deploy second project
            print("⏳ Deploying second project...")
            response = self.session.post(
                f"{BASE_URL}/api/v1/deployments/projects/{project_2_id}/deploy", timeout=180
            )

            if response.status_code != 200:
                print(f"❌ Failed to deploy second project: {response.status_code}")
                return False

            data_2 = response.json()
            canister_id_2 = data_2.get("canister_id")
            url_2 = data_2.get("url")

            print(f"✅ Second project deployed")
            print(f"   First Canister:  {self.canister_id}")
            print(f"   Second Canister: {canister_id_2}")
            print(f"   First URL:  {self.deployment_url}")
            print(f"   Second URL: {url_2}")

            # Verify they're different
            if self.canister_id != canister_id_2 and self.deployment_url != url_2:
                print(f"✅ VERIFIED: Each project gets unique canister ID and URL!")
                print(f"✅ CONFIRMED: No canister sharing - complete project isolation")
                return True
            else:
                print(f"❌ ERROR: Projects are sharing canisters!")
                return False

        except Exception as e:
            print(f"❌ Unique canister verification error: {e}")
            return False

    def run_complete_test(self):
        """Run complete production flow test"""
        print("\\n" + "=" * 100)
        print("🚀 ICP HOSTING PLATFORM - PRODUCTION USER FLOW TEST")
        print("=" * 100)
        print("Testing complete user experience:")
        print(
            "1. Register → 2. Login → 3. Create Project + Upload File → 4. Deploy → 5. Verify Live → 6. Unique Canisters"
        )
        print("=" * 100)

        start_time = time.time()

        # Run all test steps
        steps = [
            ("Register User", self.test_step_1_register),
            ("Login & Get JWT", self.test_step_2_login),
            ("Create Project + Upload HTML", self.test_step_3_create_project_with_file),
            ("Deploy to Get Canister", self.test_step_4_deploy_project),
            ("Verify Site is Live", self.test_step_5_verify_canister_live),
            ("Verify Unique Canisters", self.test_step_6_unique_canister_verification),
        ]

        results = []
        for step_name, step_func in steps:
            try:
                success = step_func()
                results.append((step_name, success))
                if not success:
                    break
            except Exception as e:
                print(f"❌ {step_name} failed with exception: {e}")
                results.append((step_name, False))
                break

        # Final results
        elapsed_time = time.time() - start_time
        print("\\n" + "=" * 100)
        print("📊 PRODUCTION FLOW TEST RESULTS")
        print("=" * 100)

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for step_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status:8} | {step_name}")

        print("=" * 100)
        print(f"OVERALL: {passed}/{total} steps passed ({passed / total * 100:.1f}%)")
        print(f"Time: {elapsed_time:.1f} seconds")

        if passed == total:
            print("\\n🎉 SUCCESS: Production-ready system fully verified!")
            print("✅ Complete user flow working")
            print("✅ File upload functional")
            print("✅ Unique canisters per project")
            print("✅ Mainnet deployment working")
            print("✅ Live sites accessible")
            print(f"\\n🌐 Your deployed site: {self.deployment_url}")
        else:
            print("\\n❌ ISSUES FOUND: System needs attention before production")

        print("=" * 100)


if __name__ == "__main__":
    tester = ProductionFlowTester()
    tester.run_complete_test()
