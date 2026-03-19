"""Comprehensive test suite for ICRC Rosetta API integration."""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.rosetta_client import RosettaClient
from app.services.auto_funding_detector import AutoFundingDetector
from app.services.icp_identity_manager import ICPIdentityManager
from app.models.user import User


class TestRosettaClient:
    """Test suite for RosettaClient."""

    def setup_method(self):
        """Setup test client."""
        self.client = RosettaClient(
            node_address="http://localhost:8082",
            canister_id="rrkah-fqaaa-aaaaa-aaaaq-cai",
            network_identifier="local",
        )

    @patch("requests.post")
    def test_network_list(self, mock_post):
        """Test network list API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "network_identifiers": [
                {"blockchain": "Internet Computer", "network": "local"}
            ]
        }
        mock_post.return_value = mock_response

        networks = self.client.get_network_list()

        assert len(networks) == 1
        assert networks[0]["blockchain"] == "Internet Computer"
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_network_status(self, mock_post):
        """Test network status API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_block_identifier": {"index": 12345, "hash": "0x123"},
            "current_block_timestamp": 1640995200000,
            "genesis_block_identifier": {"index": 0, "hash": "0x000"},
        }
        mock_post.return_value = mock_response

        status = self.client.get_network_status()

        assert status["current_block_identifier"]["index"] == 12345
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_account_balance(self, mock_post):
        """Test account balance query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "balances": [
                {
                    "value": "100000000",  # 1 ICP (8 decimals)
                    "currency": {"symbol": "ICP", "decimals": 8},
                }
            ]
        }
        mock_post.return_value = mock_response

        balance = self.client.get_account_balance("test-principal-123")

        assert len(balance["balances"]) == 1
        assert balance["balances"][0]["value"] == "100000000"
        assert balance["balances"][0]["currency"]["symbol"] == "ICP"
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_get_block(self, mock_post):
        """Test block retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "block": {
                "block_identifier": {"index": 100, "hash": "0x456"},
                "parent_block_identifier": {"index": 99, "hash": "0x455"},
                "timestamp": 1640995200000,
                "transactions": [],
            }
        }
        mock_post.return_value = mock_response

        block = self.client.get_block(100)

        assert block["block_identifier"]["index"] == 100
        mock_post.assert_called_once()

    def test_token_info_discovery(self):
        """Test automatic token info discovery."""
        # Test that client has default token info
        assert "symbol" in self.client.token_info
        assert "decimals" in self.client.token_info
        assert self.client.token_info["symbol"] == "ICP"
        assert self.client.token_info["decimals"] == 8

    def test_format_token_amount(self):
        """Test token amount formatting."""
        # 1 ICP = 100,000,000 units (8 decimals)
        formatted = self.client.format_token_amount(100000000)
        assert "1.00000000 ICP" in formatted

        # 0.5 ICP
        formatted = self.client.format_token_amount(50000000)
        assert "0.50000000 ICP" in formatted

    def test_parse_token_amount(self):
        """Test token amount parsing."""
        # Parse "1.5 ICP" to raw units
        raw_amount = self.client.parse_token_amount("1.5 ICP")
        assert raw_amount == 150000000

        # Parse "0.02 ICP"
        raw_amount = self.client.parse_token_amount("0.02 ICP")
        assert raw_amount == 2000000

    def test_principal_to_account_id(self):
        """Test principal ID to account ID conversion."""
        principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
        account_id = self.client._principal_to_account_id(principal_id)

        assert isinstance(account_id, str)
        assert len(account_id) > 0
        # Account ID should be deterministic
        account_id2 = self.client._principal_to_account_id(principal_id)
        assert account_id == account_id2

    @patch("requests.post")
    def test_search_transactions(self, mock_post):
        """Test transaction search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactions": [
                {
                    "transaction_identifier": {"hash": "0x789"},
                    "operations": [
                        {
                            "operation_identifier": {"index": 0},
                            "type": "TRANSFER",
                            "account": {"address": "test-account"},
                            "amount": {
                                "value": "10000000",
                                "currency": {"symbol": "ICP", "decimals": 8},
                            },
                        }
                    ],
                }
            ]
        }
        mock_post.return_value = mock_response

        transactions = self.client.search_transactions("test-principal")

        assert len(transactions) == 1
        assert transactions[0]["transaction_identifier"]["hash"] == "0x789"
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_api_error_handling(self, mock_post):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": {"code": 500, "message": "Internal server error"}
        }
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            self.client.get_network_list()

        assert "Rosetta API error" in str(exc_info.value)

    @patch("requests.post")
    def test_connection_error(self, mock_post):
        """Test connection error handling."""
        mock_post.side_effect = Exception("Connection refused")

        with pytest.raises(Exception) as exc_info:
            self.client.get_network_list()

        assert "Failed to connect to Rosetta API" in str(exc_info.value)


class TestAutoFundingDetector:
    """Test suite for AutoFundingDetector."""

    def setup_method(self):
        """Setup test detector."""
        self.detector = AutoFundingDetector()

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
        user.dfx_identity_name = "test_user_1_abc123"
        user.wallet_cycles_balance = "0"
        return user

    @patch("app.services.auto_funding_detector.RosettaClient")
    @patch("app.services.icp_identity_manager.ICPIdentityManager.check_wallet_balance")
    async def test_check_user_funding_status_funded(
        self, mock_balance, mock_rosetta_class, mock_user
    ):
        """Test funding status check for funded user."""
        # Mock Rosetta client
        mock_rosetta = Mock()
        mock_rosetta.get_account_balance.return_value = {
            "balances": [
                {"value": "2000000", "currency": {"symbol": "ICP", "decimals": 8}}
            ]
        }
        mock_rosetta.format_token_amount.return_value = "0.02000000 ICP"
        mock_rosetta_class.return_value = mock_rosetta

        # Mock cycles balance (funded)
        mock_balance.return_value = "50000000"  # 50M cycles

        # Mock session
        mock_session = AsyncMock()

        funding_status = await self.detector.check_user_funding_status(
            mock_session, mock_user
        )

        assert funding_status["funded"] == True
        assert funding_status["has_pending_icp"] == True
        assert funding_status["auto_convert_available"] == False  # Already funded
        assert "50,000,000 cycles" in funding_status["formatted_cycles"]

    @patch("app.services.auto_funding_detector.RosettaClient")
    @patch("app.services.icp_identity_manager.ICPIdentityManager.check_wallet_balance")
    async def test_check_user_funding_status_needs_funding(
        self, mock_balance, mock_rosetta_class, mock_user
    ):
        """Test funding status check for user needing funding."""
        # Mock Rosetta client (no ICP balance)
        mock_rosetta = Mock()
        mock_rosetta.get_account_balance.return_value = {
            "balances": [{"value": "0", "currency": {"symbol": "ICP", "decimals": 8}}]
        }
        mock_rosetta.format_token_amount.return_value = "0.00000000 ICP"
        mock_rosetta_class.return_value = mock_rosetta

        # Mock cycles balance (unfunded)
        mock_balance.return_value = "100000"  # 100K cycles (insufficient)

        mock_session = AsyncMock()

        funding_status = await self.detector.check_user_funding_status(
            mock_session, mock_user
        )

        assert funding_status["funded"] == False
        assert funding_status["has_pending_icp"] == False
        assert funding_status["auto_convert_available"] == False
        assert "minimum 0.02 ICP required" in funding_status["message"]

    @patch("app.services.auto_funding_detector.RosettaClient")
    @patch("app.services.icp_identity_manager.ICPIdentityManager.check_wallet_balance")
    async def test_check_user_funding_status_auto_convert_available(
        self, mock_balance, mock_rosetta_class, mock_user
    ):
        """Test funding status check for user with ICP to convert."""
        # Mock Rosetta client (has ICP balance)
        mock_rosetta = Mock()
        mock_rosetta.get_account_balance.return_value = {
            "balances": [
                {
                    "value": "5000000",
                    "currency": {"symbol": "ICP", "decimals": 8},
                }  # 0.05 ICP
            ]
        }
        mock_rosetta.format_token_amount.return_value = "0.05000000 ICP"
        mock_rosetta_class.return_value = mock_rosetta

        # Mock cycles balance (insufficient but has ICP)
        mock_balance.return_value = "1000000"  # 1M cycles (insufficient)

        mock_session = AsyncMock()

        funding_status = await self.detector.check_user_funding_status(
            mock_session, mock_user
        )

        assert funding_status["funded"] == False
        assert funding_status["has_pending_icp"] == True
        assert funding_status["auto_convert_available"] == True
        assert "click to convert to cycles" in funding_status["message"]

    async def test_get_funding_instructions(self, mock_user):
        """Test funding instructions generation."""
        instructions = await self.detector.get_funding_instructions(mock_user)

        assert "principal_id" in instructions
        assert instructions["principal_id"] == mock_user.principal_id
        assert "instructions" in instructions
        assert len(instructions["instructions"]) >= 4  # Should have 4+ steps
        assert "quick_links" in instructions

        # Check instruction steps
        steps = instructions["instructions"]
        step_titles = [step["title"] for step in steps]
        assert "Get Your Principal ID" in step_titles
        assert "Buy ICP Tokens" in step_titles

    def test_get_funding_message(self):
        """Test funding message generation."""
        # Test funded message
        message = self.detector._get_funding_message(True, False, 0, 50000000)
        assert "ready with" in message.lower()

        # Test needs conversion message
        message = self.detector._get_funding_message(False, True, 5000000, 1000000)
        assert "click to convert" in message.lower()

        # Test needs funding message
        message = self.detector._get_funding_message(False, False, 0, 0)
        assert "minimum 0.02 ICP" in message.lower()

    def test_network_info(self):
        """Test network info retrieval."""
        network_info = self.detector.get_network_info()

        # Should return error info if Rosetta not available
        assert "healthy" in network_info
        if not network_info["healthy"]:
            assert "error" in network_info

    def test_is_rosetta_healthy(self):
        """Test Rosetta health check."""
        healthy = self.detector.is_rosetta_healthy()
        assert isinstance(healthy, bool)


class TestIntegration:
    """Integration tests for the complete Rosetta workflow."""

    @pytest.mark.asyncio
    async def test_complete_user_funding_workflow(self):
        """Test complete user funding workflow from start to finish."""
        # This would be an integration test that requires:
        # 1. Running Rosetta API
        # 2. Test ICP tokens
        # 3. Live network connection

        # For now, we'll mock the workflow
        mock_session = AsyncMock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.principal_id = "test-principal"
        mock_user.dfx_identity_name = "test_identity"

        with patch(
            "app.services.auto_funding_detector.RosettaClient"
        ) as mock_rosetta_class:
            mock_rosetta = Mock()
            mock_rosetta.get_account_balance.return_value = {
                "balances": [
                    {"value": "2000000", "currency": {"symbol": "ICP", "decimals": 8}}
                ]
            }
            mock_rosetta.format_token_amount.return_value = "0.02000000 ICP"
            mock_rosetta_class.return_value = mock_rosetta

            detector = AutoFundingDetector()

            with patch(
                "app.services.icp_identity_manager.ICPIdentityManager.check_wallet_balance",
                return_value="1000000",
            ):
                funding_status = await detector.check_user_funding_status(
                    mock_session, mock_user
                )

                # Should detect ICP available for conversion
                assert funding_status["auto_convert_available"] == True
                assert funding_status["has_pending_icp"] == True

    def test_rosetta_error_handling(self):
        """Test error handling throughout the Rosetta integration."""
        client = RosettaClient()

        with patch("requests.post") as mock_post:
            # Test various error conditions
            mock_post.side_effect = Exception("Network error")

            with pytest.raises(Exception):
                client.get_network_list()


# Test data fixtures
@pytest.fixture
def sample_network_response():
    """Sample Rosetta network response."""
    return {
        "network_identifiers": [
            {"blockchain": "Internet Computer", "network": "mainnet"}
        ]
    }


@pytest.fixture
def sample_balance_response():
    """Sample Rosetta balance response."""
    return {
        "balances": [
            {
                "value": "100000000",  # 1 ICP
                "currency": {"symbol": "ICP", "decimals": 8, "metadata": {}},
            }
        ]
    }


@pytest.fixture
def sample_block_response():
    """Sample Rosetta block response."""
    return {
        "block": {
            "block_identifier": {"index": 1000, "hash": "0xabc123"},
            "parent_block_identifier": {"index": 999, "hash": "0xabc122"},
            "timestamp": 1640995200000,
            "transactions": [
                {
                    "transaction_identifier": {"hash": "0xdef456"},
                    "operations": [
                        {
                            "operation_identifier": {"index": 0},
                            "type": "TRANSFER",
                            "account": {"address": "account1"},
                            "amount": {
                                "value": "10000000",
                                "currency": {"symbol": "ICP", "decimals": 8},
                            },
                        }
                    ],
                }
            ],
        }
    }


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
