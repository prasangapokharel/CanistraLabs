"""Tests for unified dfx API and DfxCommand extensions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.dfxCommand import DfxCommand
from app.services.dfxRegistry import registry_summary


client = TestClient(app)


class TestDfxRegistry:
    def test_registry_has_implemented_commands(self):
        summary = registry_summary()
        assert summary["implemented"] >= 20
        assert summary["total"] > summary["implemented"]
        apis = [c["api"] for c in summary["commands"] if c["api"]]
        assert "/api/v1/dfx/canister/{canister_id}/start" in apis
        assert "/api/v1/dfx/projects/{project_id}/deploy" in apis


class TestDfxCommandExtensions:
    def test_result_success(self):
        dfx = DfxCommand(network="ic")
        r = dfx._result(0, "ok\n", "", canisterId="abc")
        assert r["success"] is True
        assert r["output"] == "ok"

    def test_result_failure(self):
        dfx = DfxCommand(network="ic")
        r = dfx._result(1, "", "boom")
        assert r["success"] is False
        assert r["error"] == "boom"

    @patch.object(DfxCommand, "_runCommand", return_value=(0, "Running", ""))
    def test_canister_start(self, mock_run):
        dfx = DfxCommand(network="ic")
        result = dfx.canisterStart("aaaaa-aa", identity="user1", network="ic")
        assert result["success"] is True
        mock_run.assert_called_once()

    @patch.object(DfxCommand, "_runCommand", return_value=(0, "", ""))
    def test_canister_delete_includes_yes(self, mock_run):
        dfx = DfxCommand(network="ic")
        dfx.canisterDelete("aaaaa-aa", identity="user1")
        args = mock_run.call_args[0][0]
        assert "--yes" in args
        assert "delete" in args


class TestDfxApiPublic:
    def test_commands_catalog(self):
        res = client.get("/api/v1/dfx/commands")
        assert res.status_code == 200
        data = res.json()
        assert data["implemented"] >= 20
        assert "commands" in data

    @patch.object(DfxCommand, "ping", return_value={"success": True, "output": "{}"})
    def test_ping(self, _mock):
        res = client.get("/api/v1/dfx/ping?network=ic")
        assert res.status_code == 200
        assert res.json()["command"] == "dfx ping ic"

    @patch.object(DfxCommand, "_runCommand", return_value=(0, "dfx 0.31.0", ""))
    def test_version(self, _mock):
        res = client.get("/api/v1/dfx/version")
        assert res.status_code == 200
        assert "0.31" in res.json()["version"]


class TestDfxApiAuth:
    def test_identity_whoami_requires_auth(self):
        res = client.get("/api/v1/dfx/identity/whoami")
        assert res.status_code == 401

    def test_canister_status_requires_auth(self):
        res = client.get("/api/v1/dfx/canister/aaaaa-aa/status")
        assert res.status_code == 401
