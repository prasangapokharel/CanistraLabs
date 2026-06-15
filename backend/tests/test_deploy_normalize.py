"""Tests for deploy response normalization."""

from app.services.dfxApiService import _serialize_deployment


def test_serialize_deployment_includes_ids():
    class Dep:
        id = 7
        status = "pending_funding"
        message = "Need cycles"
        canister_id = None
        deployment_url = None
        created_at = None
        started_at = None
        completed_at = None

    data = _serialize_deployment(Dep())
    assert data["deployment_id"] == 7
    assert data["status"] == "pending_funding"
