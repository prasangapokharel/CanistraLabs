#!/usr/bin/env python3
"""
Simple CLI for testing clean dfxCommand service.

Usage:
    python test_dfx.py status [user_id]
    python test_dfx.py balances [user_id]
    python test_dfx.py convert [user_id] [amount]
    python test_dfx.py identities
"""

import sys
import asyncio
import json
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.dfxCommand import DfxCommand
from app.database.db import async_session_maker
from app.services.auth import AuthService


class TestDfx:
    """Simple test CLI for dfxCommand service."""

    def __init__(self):
        self.dfx = DfxCommand(network="ic")

    def print_result(self, result: dict, title: str = None):
        """Pretty print result."""
        if title:
            print(f"\n🔍 {title}")
            print("=" * (len(title) + 4))
        print(json.dumps(result, indent=2, default=str))

    async def get_user(self, user_id: int):
        """Get user from database."""
        async with async_session_maker() as session:
            user = await AuthService.get_user_by_id(session, user_id)
            if not user:
                print(f"❌ User {user_id} not found")
                return None
            return user

    async def cmd_status(self, user_id: int = 37):
        """Test getUserStatus for a user."""
        user = await self.get_user(user_id)
        if not user or not user.dfx_identity_name:
            print("❌ No identity found for user")
            return

        print(f"\n🚀 User Status Test - User {user_id}")
        result = self.dfx.getUserStatus(user.dfx_identity_name)
        self.print_result(result, "User Status")

    async def cmd_balances(self, user_id: int = 37):
        """Test individual balance commands."""
        user = await self.get_user(user_id)
        if not user or not user.dfx_identity_name:
            print("❌ No identity found for user")
            return

        identity = user.dfx_identity_name
        print(f"\n💰 Balance Test - {identity}")

        # Test ICP balance
        icp = self.dfx.ledgerGetBalance(identity=identity)
        self.print_result(icp, "ICP Balance")

        # Test cycles balance
        cycles = self.dfx.cyclesGetBalance(identity=identity)
        self.print_result(cycles, "Cycles Balance")

        # Test wallet balance
        wallet = self.dfx.walletGetBalance(identity=identity)
        self.print_result(wallet, "Wallet Balance")

    async def cmd_convert(self, user_id: int = 37, amount: str = None):
        """Test ICP to cycles conversion."""
        user = await self.get_user(user_id)
        if not user or not user.dfx_identity_name:
            print("❌ No identity found for user")
            return

        identity = user.dfx_identity_name
        print(f"\n🔄 Conversion Test - {identity}")

        if amount:
            # Convert specific amount
            result = self.dfx.cyclesConvert(amount, identity=identity)
            self.print_result(result, f"Convert {amount} ICP")
        else:
            # Auto-convert
            result = self.dfx.autoConvertIcp(identity)
            self.print_result(result, "Auto-Convert ICP")

    def cmd_identities(self):
        """Test identity list."""
        print("\n🆔 Identity List Test")
        result = self.dfx.identityList()
        self.print_result(result, "All Identities")

        # Test whoami
        whoami = self.dfx.identityWhoami()
        self.print_result(whoami, "Current Identity")

    async def run(self, args: list):
        """Run test command."""
        if not args:
            print("Available commands: status, balances, convert, identities")
            return

        command = args[0]

        if command == "status":
            user_id = int(args[1]) if len(args) > 1 else 37
            await self.cmd_status(user_id)
        elif command == "balances":
            user_id = int(args[1]) if len(args) > 1 else 37
            await self.cmd_balances(user_id)
        elif command == "convert":
            user_id = int(args[1]) if len(args) > 1 else 37
            amount = args[2] if len(args) > 2 else None
            await self.cmd_convert(user_id, amount)
        elif command == "identities":
            self.cmd_identities()
        else:
            print(f"❌ Unknown command: {command}")


async def main():
    """Main test entry point."""
    test = TestDfx()
    await test.run(sys.argv[1:])


if __name__ == "__main__":
    asyncio.run(main())
