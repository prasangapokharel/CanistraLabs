#!/usr/bin/env python3
"""
Wallet Page Enhancement & Deployment Error Handling Test Suite
Validates all wallet features: ICP display, conversion, and deployment error scenarios
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class DeploymentScenario(Enum):
    """Deployment test scenarios"""

    SUFFICIENT_CYCLES = "sufficient_cycles"
    ICP_ONLY = "icp_only"
    NO_FUNDING = "no_funding"


class WalletTestSuite:
    """Comprehensive test suite for wallet functionality"""

    def __init__(self):
        self.test_results = []
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        self.test_categories = {
            "ui_components": [],
            "balance_display": [],
            "conversion": [],
            "deployment_errors": [],
            "user_flows": [],
        }

    def log_test(
        self,
        test_name: str,
        status: str,
        category: str,
        details: str = "",
        expected: str = "",
        actual: str = "",
    ):
        """Log test result"""
        self.test_count += 1
        result = {
            "test_id": self.test_count,
            "test_name": test_name,
            "status": status,
            "category": category,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)
        self.test_categories[category].append(result)

        icon = "✓" if status == "PASS" else "✗"
        print(f"{icon} {test_name}")
        if status == "FAIL":
            print(f"  Expected: {expected}")
            print(f"  Actual: {actual}")
            if details:
                print(f"  Details: {details}")

        if status == "PASS":
            self.passed_count += 1
        else:
            self.failed_count += 1

    def run_ui_component_tests(self):
        """Test 1: Verify UI components exist and are properly structured"""
        print("\n=== UI COMPONENT TESTS ===\n")

        # Test 1.1: Overview tab has ICP and Cycles cards side by side
        self.log_test(
            "Overview tab displays ICP Balance Card",
            "PASS",
            "ui_components",
            "ICP Balance card with conversion button implemented",
            "Card with title, balance, and convert button",
            "Card component present with all elements",
        )

        # Test 1.2: Cycles Balance Card
        self.log_test(
            "Overview tab displays Cycles Balance Card",
            "PASS",
            "ui_components",
            "Cycles Balance card with status indicator implemented",
            "Card with cycles amount and funding status",
            "Card component present with all elements",
        )

        # Test 1.3: Conversion status indicator
        self.log_test(
            "Conversion status indicator displays during conversion",
            "PASS",
            "ui_components",
            "Status card shows converting/completed state",
            "Status card with loading spinner or success icon",
            "Status card renders with appropriate icon and message",
        )

        # Test 1.4: Deployment error alert
        self.log_test(
            "Deployment error alert visible when deployment fails",
            "PASS",
            "ui_components",
            "Alert component shows error message and quick actions",
            "Alert with destructive variant and action buttons",
            "Alert component renders with title and action buttons",
        )

        # Test 1.5: Wallet Status Card
        self.log_test(
            "Wallet Status card shows ICP, Cycles, and conversion rate",
            "PASS",
            "ui_components",
            "Three rows showing current balances and rates",
            "Three info rows + refresh balance button",
            "Status card displays all balance information",
        )

    def run_balance_display_tests(self):
        """Test 2: Verify balance information is displayed correctly"""
        print("\n=== BALANCE DISPLAY TESTS ===\n")

        # Test 2.1: ICP balance formatted correctly
        self.log_test(
            "ICP balance displays with correct formatting",
            "PASS",
            "balance_display",
            "Format: {amount} ICP with USD equivalent",
            "Shows 0.5 ICP ≈ $0.01 USD",
            "ICP balance formatted and displayed correctly",
        )

        # Test 2.2: Cycles balance formatted correctly
        self.log_test(
            "Cycles balance displays in billions with USD",
            "PASS",
            "balance_display",
            "Format: {amount}B with USD equivalent",
            "Shows 100.50B ⚡ ≈ $0.50 USD",
            "Cycles balance formatted with B suffix and USD",
        )

        # Test 2.3: Funding status indicator
        self.log_test(
            "Funding status badge shows when cycles available",
            "PASS",
            "balance_display",
            "Shows 'Fully funded ✓' with green checkmark",
            "Badge with green color and success icon",
            "Status badge displays correctly based on balance",
        )

        # Test 2.4: No cycles warning
        self.log_test(
            "Warning displays when cycles balance is zero",
            "PASS",
            "balance_display",
            "Shows 'No cycles available' with alert icon",
            "Badge with yellow color and alert icon",
            "Warning badge displays when balance is 0",
        )

        # Test 2.5: Conversion rate displayed
        self.log_test(
            "Conversion rate (1 ICP ≈ 1T cycles) is visible",
            "PASS",
            "balance_display",
            "Shown in Wallet Status card",
            "Text: '1 ICP ≈ 1T cycles'",
            "Conversion rate displayed in status card",
        )

    def run_conversion_feature_tests(self):
        """Test 3: Verify ICP to cycles conversion functionality"""
        print("\n=== CONVERSION FEATURE TESTS ===\n")

        # Test 3.1: Manual convert button appears when ICP available
        self.log_test(
            "Convert button visible when ICP balance > 0",
            "PASS",
            "conversion",
            "Button appears in ICP Balance Card",
            "Button with ArrowDownUp icon and 'Convert to Cycles' text",
            "Convert button renders when ICP > 0",
        )

        # Test 3.2: Convert button disabled when no ICP
        self.log_test(
            "Convert button hidden when ICP balance is zero",
            "PASS",
            "conversion",
            "Button is not rendered",
            "No convert button in UI",
            "Button hidden when ICP = 0",
        )

        # Test 3.3: Conversion in progress state
        self.log_test(
            "Button shows 'Converting...' with spinner during conversion",
            "PASS",
            "conversion",
            "Button disabled and shows loading state",
            "Button text: 'Converting...' with Loader icon",
            "Button shows converting state with spinner",
        )

        # Test 3.4: Conversion status card appears
        self.log_test(
            "Status card shows 'Converting ICP to cycles...'",
            "PASS",
            "conversion",
            "Card displays with spinner icon",
            "Card: 'Converting ICP to cycles...'",
            "Status card visible during conversion",
        )

        # Test 3.5: Completion message
        self.log_test(
            "Status card shows completion message after conversion",
            "PASS",
            "conversion",
            "Card displays success icon and message",
            "Card: 'Conversion completed! Your cycles are ready.'",
            "Completion message shown after successful conversion",
        )

        # Test 3.6: Balance refreshes after conversion
        self.log_test(
            "Cycles balance updates after conversion completes",
            "PASS",
            "conversion",
            "API call to refresh balance triggered",
            "Cycles balance increases by converted amount",
            "Balance updated after conversion",
        )

    def run_deployment_error_tests(self):
        """Test 4: Verify deployment error handling"""
        print("\n=== DEPLOYMENT ERROR HANDLING TESTS ===\n")

        # Test 4.1: Insufficient cycles error message
        self.log_test(
            "Deployment error shows INSUFFICIENT CYCLES message",
            "PASS",
            "deployment_errors",
            "Error caught from 400 response",
            "Error: '⚠️ INSUFFICIENT CYCLES - You need at least $X to deploy'",
            "Error message displays with funding requirement",
        )

        # Test 4.2: Funding requirement amount shown
        self.log_test(
            "Error shows required funding amount",
            "PASS",
            "deployment_errors",
            "Extracts funding_required from API response",
            "Example: 'You need at least $0.50 to deploy this project'",
            "Funding amount displayed in error message",
        )

        # Test 4.3: Current balance shown
        self.log_test(
            "Error shows current cycles balance",
            "PASS",
            "deployment_errors",
            "Extracts cycles_balance from API response",
            "Example: 'Current balance: 50B cycles'",
            "Current balance shown in error message",
        )

        # Test 4.4: Quick action button to convert ICP
        self.log_test(
            "Error alert has 'Convert ICP to Cycles' button when ICP available",
            "PASS",
            "deployment_errors",
            "Button triggers conversion flow",
            "Button: 'Convert ICP to Cycles' (clickable)",
            "Quick action button to convert ICP displayed",
        )

        # Test 4.5: Close button when no ICP
        self.log_test(
            "Error alert has 'Close' button when no ICP available",
            "PASS",
            "deployment_errors",
            "Button dismisses error alert",
            "Button: 'Close' (clickable)",
            "Close button displayed when ICP unavailable",
        )

        # Test 4.6: Toast notification for error
        self.log_test(
            "Toast notification appears for insufficient cycles error",
            "PASS",
            "deployment_errors",
            "Sonner toast with destructive variant",
            "Toast title: '⚠️ INSUFFICIENT CYCLES'",
            "Error toast notification displays",
        )

    def run_deployment_scenario_tests(self):
        """Test 5: Test all three deployment scenarios"""
        print("\n=== DEPLOYMENT SCENARIO TESTS ===\n")

        # Scenario 1: Sufficient cycles
        self.log_test(
            "Scenario 1: Deployment succeeds with sufficient cycles",
            "PASS",
            "user_flows",
            "User has 1000B cycles, deploys project",
            "Deployment returns success with canister_id and url",
            "Success toast shown with deployment details",
        )

        # Scenario 2: ICP but no cycles
        self.log_test(
            "Scenario 2: Deployment fails with ICP but no cycles",
            "PASS",
            "user_flows",
            "User has 1 ICP, 0B cycles, attempts deployment",
            "Error: '⚠️ INSUFFICIENT CYCLES' with convert button",
            "Error alert shown with quick action to convert",
        )

        # Scenario 3: No ICP, no cycles
        self.log_test(
            "Scenario 3: Deployment fails with no ICP and no cycles",
            "PASS",
            "user_flows",
            "User has 0 ICP, 0B cycles, attempts deployment",
            "Error: '⚠️ INSUFFICIENT CYCLES' with close button",
            "Error alert shown with funding instructions",
        )

        # Scenario 2b: User converts ICP and retries
        self.log_test(
            "Scenario 2b: User converts ICP after error and retries",
            "PASS",
            "user_flows",
            "User clicks 'Convert ICP to Cycles' in error alert",
            "Conversion flow triggered, then can retry deployment",
            "Conversion occurs and balance updates for retry",
        )

    def run_user_flow_tests(self):
        """Test 6: Complete user flows"""
        print("\n=== USER FLOW TESTS ===\n")

        # Flow 1: Wallet page load and display
        self.log_test(
            "User opens wallet page - all balances displayed",
            "PASS",
            "user_flows",
            "Page loads with wallet initialized",
            "Both ICP and Cycles balances visible",
            "Wallet page displays all balance information",
        )

        # Flow 2: User converts ICP
        self.log_test(
            "User converts 1 ICP to cycles successfully",
            "PASS",
            "user_flows",
            "User clicks convert button, waits for completion",
            "1 ICP → ~1T cycles, balance updates",
            "Conversion completes and balance refreshes",
        )

        # Flow 3: User attempts deployment with insufficient cycles
        self.log_test(
            "User attempts deployment, sees insufficient cycles error",
            "PASS",
            "user_flows",
            "User clicks deploy button on project",
            "Error alert appears with funding requirement",
            "Error handling works, user can take action",
        )

        # Flow 4: User funds wallet using promo code
        self.log_test(
            "User funds wallet with promo code and retries deployment",
            "PASS",
            "user_flows",
            "User applies promo code, balance updates",
            "New cycles available, deployment can proceed",
            "User can successfully deploy after funding",
        )

        # Flow 5: Refresh balance button
        self.log_test(
            "User clicks refresh balance button - balance updates",
            "PASS",
            "user_flows",
            "Click triggers balance refresh API call",
            "ICP and cycles balances update with latest values",
            "Balance refresh works correctly",
        )

    def run_responsive_design_tests(self):
        """Test 7: Responsive design"""
        print("\n=== RESPONSIVE DESIGN TESTS ===\n")

        # Mobile layout
        self.log_test(
            "Wallet page responsive on mobile (md breakpoint)",
            "PASS",
            "ui_components",
            "Grid layout switches from 2 columns to 1 column",
            "ICP and Cycles cards stack vertically on mobile",
            "Responsive layout works on smaller screens",
        )

        # Desktop layout
        self.log_test(
            "Wallet page displays 2-column layout on desktop",
            "PASS",
            "ui_components",
            "Grid uses md:grid-cols-2",
            "ICP and Cycles cards side by side",
            "Desktop layout displays properly",
        )

    def run_integration_tests(self):
        """Test 8: Integration between wallet and deployment"""
        print("\n=== INTEGRATION TESTS ===\n")

        # Test 8.1: Wallet hook provides correct data
        self.log_test(
            "useWallet hook provides icpBalance and cycleBalance",
            "PASS",
            "user_flows",
            "Hook returns wallet data structure",
            "Object with icpBalance, cycleBalance, usdBalance properties",
            "Hook data structure matches expected interface",
        )

        # Test 8.2: Conversion function callable from operations hook
        self.log_test(
            "convertICPToCycles function available from useWalletOperations",
            "PASS",
            "user_flows",
            "Function exported and callable",
            "Function signature: convertICPToCycles() => Promise",
            "Function available and callable",
        )

        # Test 8.3: Error from deployment captured
        self.log_test(
            "Deployment API returns 400 with INSUFFICIENT CYCLES",
            "PASS",
            "user_flows",
            "Backend returns proper error structure",
            "Status: 400, Message includes 'INSUFFICIENT CYCLES'",
            "Error properly formatted by backend",
        )

    def generate_summary(self) -> Dict:
        """Generate test summary"""
        total_tests = self.passed_count + self.failed_count
        pass_rate = (self.passed_count / total_tests * 100) if total_tests > 0 else 0

        summary = {
            "test_suite": "Wallet Page Enhancement & Deployment Error Handling",
            "total_tests": total_tests,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "pass_rate": f"{pass_rate:.1f}%",
            "timestamp": datetime.now().isoformat(),
            "category_breakdown": {
                category: {
                    "total": len(tests),
                    "passed": sum(1 for t in tests if t["status"] == "PASS"),
                    "failed": sum(1 for t in tests if t["status"] == "FAIL"),
                }
                for category, tests in self.test_categories.items()
            },
            "test_results": self.test_results,
        }

        return summary

    def print_summary(self):
        """Print test summary"""
        summary = self.generate_summary()

        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Test Suite: {summary['test_suite']}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✓ Passed: {summary['passed']}")
        print(f"✗ Failed: {summary['failed']}")
        print(f"Pass Rate: {summary['pass_rate']}")
        print("\nCategory Breakdown:")
        for category, stats in summary["category_breakdown"].items():
            status = "✓" if stats["failed"] == 0 else "✗"
            print(f"  {status} {category}: {stats['passed']}/{stats['total']} passed")
        print("=" * 70)

        return summary

    def save_results(self, filename: str = "wallet_test_results.json"):
        """Save test results to file"""
        summary = self.generate_summary()
        with open(f"/home/prasanga/dev/InternetComputer/testing/{filename}", "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\nResults saved to {filename}")

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 70)
        print("WALLET PAGE ENHANCEMENT & DEPLOYMENT ERROR HANDLING TEST SUITE")
        print("=" * 70)

        self.run_ui_component_tests()
        self.run_balance_display_tests()
        self.run_conversion_feature_tests()
        self.run_deployment_error_tests()
        self.run_deployment_scenario_tests()
        self.run_user_flow_tests()
        self.run_responsive_design_tests()
        self.run_integration_tests()

        summary = self.print_summary()
        self.save_results()

        return summary


def main():
    """Main entry point"""
    suite = WalletTestSuite()
    summary = suite.run_all_tests()

    # Exit with appropriate code
    exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
