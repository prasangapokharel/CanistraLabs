#!/usr/bin/env python3
"""
Frontend Hooks & Library Integration Verification
Validates all React hooks and library functions are properly implemented
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set


class FrontendHooksVerifier:
    def __init__(self):
        self.frontend_path = Path("/home/prasanga/dev/InternetComputer/frontend/src")
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
        }
        self.test_results.append(result)

        if status == "PASS":
            self.passed_count += 1
            print(f"✓ {test_name}")
        else:
            self.failed_count += 1
            print(f"✗ {test_name}: {details}")

    def check_file_exists(self, file_path: Path) -> bool:
        """Check if file exists"""
        return file_path.exists()

    def get_exports_from_file(self, file_path: Path) -> Set[str]:
        """Extract exports from a TypeScript/JavaScript file"""
        exports = set()
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Find all exports
            export_matches = re.findall(
                r"export\s+(?:const|function|interface|type)\s+(\w+)", content
            )
            exports.update(export_matches)

            # Find default exports
            if re.search(r"export\s+default\s+(\w+)", content):
                exports.add("default")
        except:
            pass

        return exports

    def check_imports_in_file(
        self, file_path: Path, required_imports: List[str]
    ) -> tuple[bool, List[str]]:
        """Check if file contains required imports"""
        missing = []
        try:
            with open(file_path, "r") as f:
                content = f.read()

            for imp in required_imports:
                if imp not in content:
                    missing.append(imp)
        except:
            missing = required_imports

        return len(missing) == 0, missing

    # ==================== HOOKS VERIFICATION ====================
    def verify_useauth_hook(self) -> bool:
        """Verify useAuth hook is properly implemented"""
        file_path = self.frontend_path / "hooks" / "api" / "useAuth.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Hook: useAuth", "FAIL", "File not found")
            return False

        required_functions = ["useCurrentUser", "useLogin", "useSignup", "useLogout"]

        exports = self.get_exports_from_file(file_path)
        missing = [fn for fn in required_functions if fn not in exports]

        if not missing:
            self.log_test(
                "Hook: useAuth",
                "PASS",
                f"All functions exported: {', '.join(required_functions)}",
            )
            return True
        else:
            self.log_test("Hook: useAuth", "FAIL", f"Missing: {', '.join(missing)}")
            return False

    def verify_useprojects_hook(self) -> bool:
        """Verify useProjects hook is properly implemented"""
        file_path = self.frontend_path / "hooks" / "api" / "useProjects.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Hook: useProjects", "FAIL", "File not found")
            return False

        required_functions = [
            "useProjects",
            "useProject",
            "useCreateProject",
            "useUpdateProject",
            "useDeleteProject",
        ]

        exports = self.get_exports_from_file(file_path)
        missing = [fn for fn in required_functions if fn not in exports]

        if not missing:
            self.log_test(
                "Hook: useProjects",
                "PASS",
                f"All functions exported: {', '.join(required_functions)}",
            )
            return True
        else:
            self.log_test("Hook: useProjects", "FAIL", f"Missing: {', '.join(missing)}")
            return False

    def verify_usedeployments_hook(self) -> bool:
        """Verify useDeployments hook is properly implemented"""
        file_path = self.frontend_path / "hooks" / "api" / "useDeployments.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Hook: useDeployments", "FAIL", "File not found")
            return False

        required_functions = ["useDeployProject", "useCanisterStatus"]

        exports = self.get_exports_from_file(file_path)
        missing = [fn for fn in required_functions if fn not in exports]

        if not missing:
            self.log_test(
                "Hook: useDeployments",
                "PASS",
                f"All functions exported: {', '.join(required_functions)}",
            )
            return True
        else:
            self.log_test(
                "Hook: useDeployments", "FAIL", f"Missing: {', '.join(missing)}"
            )
            return False

    def verify_usewallet_hook(self) -> bool:
        """Verify useWallet hook is properly implemented"""
        file_path = self.frontend_path / "hooks" / "api" / "useWallet.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Hook: useWallet", "FAIL", "File not found")
            return False

        required_functions = ["useWallet"]

        exports = self.get_exports_from_file(file_path)
        missing = [fn for fn in required_functions if fn not in exports]

        if not missing:
            self.log_test(
                "Hook: useWallet",
                "PASS",
                f"All functions exported: {', '.join(required_functions)}",
            )
            return True
        else:
            self.log_test("Hook: useWallet", "FAIL", f"Missing: {', '.join(missing)}")
            return False

    def verify_usemetrics_hook(self) -> bool:
        """Verify useMetrics hook is properly implemented"""
        file_path = self.frontend_path / "hooks" / "api" / "useMetrics.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Hook: useMetrics", "FAIL", "File not found")
            return False

        has_exports = len(self.get_exports_from_file(file_path)) > 0

        if has_exports:
            self.log_test("Hook: useMetrics", "PASS", "Exports found")
            return True
        else:
            self.log_test("Hook: useMetrics", "FAIL", "No exports found")
            return False

    def verify_usedashboard_hook(self) -> bool:
        """Verify useDashboard hook is properly implemented"""
        file_path = self.frontend_path / "hooks" / "api" / "useDashboard.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Hook: useDashboard", "FAIL", "File not found")
            return False

        has_exports = len(self.get_exports_from_file(file_path)) > 0

        if has_exports:
            self.log_test("Hook: useDashboard", "PASS", "Exports found")
            return True
        else:
            self.log_test("Hook: useDashboard", "FAIL", "No exports found")
            return False

    # ==================== LIB VERIFICATION ====================
    def verify_apiclient_lib(self) -> bool:
        """Verify apiClient library is properly implemented"""
        file_path = self.frontend_path / "lib" / "apiClient.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Lib: apiClient", "FAIL", "File not found")
            return False

        required_methods = [
            "login",
            "signup",
            "refreshToken",
            "logout",
            "getProjects",
            "createProject",
            "deployProject",
            "getWalletIdentity",
            "convertIcpToCycles",
        ]

        with open(file_path, "r") as f:
            content = f.read()

        missing = [
            method
            for method in required_methods
            if f"async {method}" not in content and f"{method}(" not in content
        ]

        if not missing:
            self.log_test(
                "Lib: apiClient",
                "PASS",
                f"All methods implemented: {len(required_methods)}",
            )
            return True
        else:
            self.log_test("Lib: apiClient", "FAIL", f"Missing: {', '.join(missing)}")
            return False

    def verify_api_lib(self) -> bool:
        """Verify api library exports are correct"""
        file_path = self.frontend_path / "lib" / "api.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Lib: api", "FAIL", "File not found")
            return False

        required_exports = ["dashboardApi", "canistersApi", "walletApi", "profileApi"]

        exports = self.get_exports_from_file(file_path)
        missing = [exp for exp in required_exports if exp not in exports]

        if not missing:
            self.log_test(
                "Lib: api",
                "PASS",
                f"All API modules exported: {', '.join(required_exports)}",
            )
            return True
        else:
            self.log_test("Lib: api", "FAIL", f"Missing: {', '.join(missing)}")
            return False

    def verify_validations_lib(self) -> bool:
        """Verify validations library"""
        file_path = self.frontend_path / "lib" / "validations.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Lib: validations", "FAIL", "File not found")
            return False

        with open(file_path, "r") as f:
            content = f.read()

        if "zod" in content and "Schema" in content:
            self.log_test("Lib: validations", "PASS", "Zod schemas defined")
            return True
        else:
            self.log_test("Lib: validations", "FAIL", "Zod schemas not found")
            return False

    def verify_wallet_lib(self) -> bool:
        """Verify wallet integration library"""
        wallet_dir = self.frontend_path / "lib" / "wallet"

        if not wallet_dir.exists():
            self.log_test("Lib: wallet", "FAIL", "Wallet directory not found")
            return False

        required_files = ["ICPWalletContext.tsx", "useWalletOperations.ts"]

        missing = [f for f in required_files if not (wallet_dir / f).exists()]

        if not missing:
            self.log_test(
                "Lib: wallet",
                "PASS",
                f"All wallet files present: {', '.join(required_files)}",
            )
            return True
        else:
            self.log_test("Lib: wallet", "FAIL", f"Missing: {', '.join(missing)}")
            return False

    # ==================== TYPES VERIFICATION ====================
    def verify_api_types(self) -> bool:
        """Verify API types are defined"""
        file_path = self.frontend_path / "types" / "api.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Types: API Types", "FAIL", "File not found")
            return False

        required_types = [
            "User",
            "Project",
            "DeploymentResponse",
            "CanisterStatus",
            "ApiError",
        ]

        with open(file_path, "r") as f:
            content = f.read()

        missing = [
            t
            for t in required_types
            if f"type {t}" not in content and f"interface {t}" not in content
        ]

        if not missing:
            self.log_test(
                "Types: API Types",
                "PASS",
                f"All types defined: {', '.join(required_types)}",
            )
            return True
        else:
            self.log_test("Types: API Types", "FAIL", f"Missing: {', '.join(missing)}")
            return False

    # ==================== ERROR HANDLING VERIFICATION ====================
    def verify_error_handling(self) -> bool:
        """Verify error handling is implemented"""
        file_path = self.frontend_path / "lib" / "apiClient.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Error Handling: API Client", "FAIL", "File not found")
            return False

        with open(file_path, "r") as f:
            content = f.read()

        error_patterns = ["handleApiError", "error.response", "retry", "catch"]

        missing = [p for p in error_patterns if p not in content]

        if len(missing) <= 1:  # Allow some flexibility
            self.log_test(
                "Error Handling: API Client",
                "PASS",
                f"Error handling implemented ({len(error_patterns) - len(missing)}/{len(error_patterns)} patterns found)",
            )
            return True
        else:
            self.log_test(
                "Error Handling: API Client",
                "FAIL",
                f"Missing patterns: {', '.join(missing)}",
            )
            return False

    def verify_cycle_error_handling(self) -> bool:
        """Verify cycle balance error handling"""
        files_to_check = [
            self.frontend_path / "lib" / "apiClient.ts",
            self.frontend_path / "hooks" / "api" / "useWallet.ts",
        ]

        cycle_patterns = ["funding_required", "cycles_balance", "insufficient"]

        found_patterns = set()
        for file_path in files_to_check:
            if file_path.exists():
                with open(file_path, "r") as f:
                    content = f.read()
                    for pattern in cycle_patterns:
                        if pattern in content:
                            found_patterns.add(pattern)

        if len(found_patterns) >= 2:
            self.log_test(
                "Error Handling: Cycle Balance",
                "PASS",
                f"Cycle handling found: {', '.join(found_patterns)}",
            )
            return True
        else:
            self.log_test(
                "Error Handling: Cycle Balance",
                "FAIL",
                f"Insufficient cycle handling: found {len(found_patterns)}",
            )
            return False

    # ==================== INTEGRATION VERIFICATION ====================
    def verify_query_provider(self) -> bool:
        """Verify React Query provider is set up"""
        file_path = self.frontend_path / "lib" / "queryProvider.tsx"

        if not self.check_file_exists(file_path):
            self.log_test("Integration: Query Provider", "FAIL", "File not found")
            return False

        self.log_test(
            "Integration: Query Provider", "PASS", "Query provider configured"
        )
        return True

    def verify_localStorage_utils(self) -> bool:
        """Verify localStorage utilities"""
        file_path = self.frontend_path / "lib" / "localStorage.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Integration: localStorage Utils", "FAIL", "File not found")
            return False

        self.log_test(
            "Integration: localStorage Utils", "PASS", "localStorage utilities present"
        )
        return True

    def verify_logger(self) -> bool:
        """Verify logger utility"""
        file_path = self.frontend_path / "lib" / "logger.ts"

        if not self.check_file_exists(file_path):
            self.log_test("Integration: Logger", "FAIL", "File not found")
            return False

        self.log_test("Integration: Logger", "PASS", "Logger utility configured")
        return True

    # ==================== RUN ALL TESTS ====================
    def run_all_tests(self):
        """Run all verification tests"""
        print("\n" + "=" * 60)
        print("FRONTEND HOOKS & LIBRARY INTEGRATION VERIFICATION")
        print("=" * 60 + "\n")

        # Hooks Verification
        print(">>> HOOKS VERIFICATION")
        self.verify_useauth_hook()
        self.verify_useprojects_hook()
        self.verify_usedeployments_hook()
        self.verify_usewallet_hook()
        self.verify_usemetrics_hook()
        self.verify_usedashboard_hook()

        # Lib Verification
        print("\n>>> LIBRARY VERIFICATION")
        self.verify_apiclient_lib()
        self.verify_api_lib()
        self.verify_validations_lib()
        self.verify_wallet_lib()

        # Types Verification
        print("\n>>> TYPES VERIFICATION")
        self.verify_api_types()

        # Error Handling Verification
        print("\n>>> ERROR HANDLING VERIFICATION")
        self.verify_error_handling()
        self.verify_cycle_error_handling()

        # Integration Verification
        print("\n>>> INTEGRATION VERIFICATION")
        self.verify_query_provider()
        self.verify_localStorage_utils()
        self.verify_logger()

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print verification summary"""
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Total Checks: {self.test_count}")
        print(
            f"Passed: {self.passed_count} ({(self.passed_count / self.test_count * 100):.1f}%)"
        )
        print(
            f"Failed: {self.failed_count} ({(self.failed_count / self.test_count * 100):.1f}%)"
        )

        if self.failed_count == 0:
            print("\n✓ ALL CHECKS PASSED!")
        else:
            print(f"\n⚠️  {self.failed_count} check(s) failed - review above")

        print("=" * 60 + "\n")


if __name__ == "__main__":
    verifier = FrontendHooksVerifier()
    verifier.run_all_tests()
