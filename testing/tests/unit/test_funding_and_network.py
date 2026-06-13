"""Unit tests for canister network detection and dfx error parsing."""

import pytest

from app.utils.canisterNetwork import (
    is_local_canister_id,
    network_for_canister,
)
from app.utils.dfxErrors import parse_dfx_error
from app.utils.cycleRequirements import funding_requirements, deploy_ready


class TestCanisterNetwork:
    def test_local_ids(self):
        assert is_local_canister_id("uxrrr-q7777-77774-qaaaq-cai")
        assert is_local_canister_id("m74gv-ax777-77777-aaarq-cai")
        assert network_for_canister("jkexm-5x777-77777-aaapq-cai") == "local"

    def test_mainnet_ids(self):
        assert not is_local_canister_id("qjtxq-xaaaa-aaaae-ada4q-cai")
        assert network_for_canister("qjtxq-xaaaa-aaaae-ada4q-cai") == "ic"


class TestDfxErrors:
    def test_canister_not_found(self):
        raw = "canister_not_found: The specified canister does not exist"
        parsed = parse_dfx_error(raw)
        assert parsed["error_code"] == "canister_not_found"
        assert "does not exist" in parsed["message"]

    def test_insufficient_cycles(self):
        parsed = parse_dfx_error("Error: Insufficient cycles balance to create the canister.")
        assert parsed["error_code"] == "insufficient_cycles"


class TestCycleRequirements:
    def test_mainnet_deploy_not_ready_at_2bc(self):
        req = funding_requirements(2_000_000_000, 0)
        assert not deploy_ready(2_000_000_000)
        assert req["cycles_shortfall"] != "0"

    def test_mainnet_deploy_ready_at_600bc(self):
        assert deploy_ready(600_000_000_000)
