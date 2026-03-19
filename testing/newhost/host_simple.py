#!/usr/bin/env python3
"""
Simplified Dynamic Host Testing Script
Tests: signup → create project → verify API working
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

class SimpleHostTest:
    def __init__(self):
        self.token = None
        self.refresh_token = None
        self.project_id = None
        self.results = []
    
    def log(self, step, status, msg):
        symbol = "✅" if status == "PASS" else "❌"
        print(f"{symbol} {step:20} | {msg}")
        self.results.append({"step": step, "status": status, "msg": msg})
    
    def test_signup(self):
        """Test signup"""
        try:
            ts = int(datetime.now().timestamp() * 1000)
            response = requests.post(
                f"{API_BASE}/auth/signup",
                json={
                    "email": f"test{ts}@example.com",
                    "password": "TestPass123!",
                    "username": f"user{ts}"
                },
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                if self.token:
                    self.log("SIGNUP", "PASS", "User created with JWT auth token")
                    return True
            
            self.log("SIGNUP", "FAIL", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log("SIGNUP", "FAIL", str(e))
            return False
    
    def test_create_project(self):
        """Test project creation"""
        if not self.token:
            self.log("CREATE_PROJECT", "FAIL", "No token available")
            return False
        
        try:
            response = requests.post(
                f"{API_BASE}/projects/",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "name": f"Test Project {datetime.now().timestamp()}",
                    "description": "Testing dynamic hosting"
                },
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                # Handle both data formats
                if isinstance(data, dict):
                    project_data = data.get("data", data)
                    self.project_id = project_data.get("id") if isinstance(project_data, dict) else None
                    
                if self.project_id:
                    self.log("CREATE_PROJECT", "PASS", f"Project created (ID: {self.project_id})")
                    return True
            
            self.log("CREATE_PROJECT", "FAIL", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log("CREATE_PROJECT", "FAIL", str(e))
            return False
    
    def test_list_projects(self):
        """Test listing projects"""
        if not self.token:
            self.log("LIST_PROJECTS", "FAIL", "No token")
            return False
        
        try:
            response = requests.get(
                f"{API_BASE}/projects/",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Handle both formats
                projects = data.get("data", data) if isinstance(data, dict) else data
                count = len(projects) if isinstance(projects, list) else 0
                self.log("LIST_PROJECTS", "PASS", f"Retrieved {count} project(s)")
                return True
            
            self.log("LIST_PROJECTS", "FAIL", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log("LIST_PROJECTS", "FAIL", str(e))
            return False
    
    def test_auth_refresh(self):
        """Test token refresh"""
        if not self.refresh_token:
            self.log("REFRESH_TOKEN", "FAIL", "No refresh token")
            return False
        
        try:
            response = requests.post(
                f"{API_BASE}/auth/refresh",
                headers={"Authorization": f"Bearer {self.refresh_token}"},
                json={},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                new_token = data.get("access_token")
                if new_token:
                    self.log("REFRESH_TOKEN", "PASS", "New access token generated")
                    return True
            
            self.log("REFRESH_TOKEN", "FAIL", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log("REFRESH_TOKEN", "FAIL", str(e))
            return False
    
    def test_get_project(self):
        """Test getting specific project"""
        if not self.token or not self.project_id:
            self.log("GET_PROJECT", "SKIP", "No project to retrieve")
            return True
        
        try:
            response = requests.get(
                f"{API_BASE}/projects/{self.project_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("GET_PROJECT", "PASS", f"Retrieved project details")
                return True
            
            self.log("GET_PROJECT", "FAIL", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log("GET_PROJECT", "FAIL", str(e))
            return False
    
    def run(self):
        print("\n" + "="*70)
        print("🧪 ICP HOSTING PLATFORM - DYNAMIC HOST TEST")
        print("="*70 + "\n")
        
        print("📋 Testing API Endpoints:")
        print("   1. User authentication (signup)")
        print("   2. Project management (create)")
        print("   3. Project retrieval (list & get)")
        print("   4. Token management (refresh)")
        print("\n" + "-"*70 + "\n")
        
        # Run all tests
        r1 = self.test_signup()
        r2 = self.test_create_project() if r1 else False
        r3 = self.test_list_projects() if r2 else False
        r4 = self.test_get_project() if r2 else False
        r5 = self.test_auth_refresh() if r1 else False
        
        # Summary
        print("\n" + "="*70)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        
        if passed == total:
            print(f"✅ ALL TESTS PASSED! ({passed}/{total})")
            print("\n📊 PLATFORM STATUS:")
            print("   ✅ User Authentication: Working")
            print("   ✅ Project Management: Working")
            print("   ✅ API Endpoints: Working")
            print("   ✅ JWT Tokens: Working")
            print("\n🚀 Ready for dynamic deployments!")
        else:
            print(f"⚠️  {passed}/{total} tests passed")
        
        print("="*70 + "\n")
        
        return passed == total

if __name__ == "__main__":
    tester = SimpleHostTest()
    success = tester.run()
    exit(0 if success else 1)
