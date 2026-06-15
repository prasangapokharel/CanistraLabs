"""Async service tests for dfx API service layer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.dfxApiService import DfxApiService


@pytest.mark.asyncio
async def test_verify_canister_owner_not_found():
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result_mock)

    with pytest.raises(HTTPException) as exc:
        await DfxApiService._verify_canister_owner(session, "bad-id", 1)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_user_with_identity_missing():
    session = AsyncMock()
    with patch(
        "app.services.dfxApiService.AuthService.get_user_by_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc:
            await DfxApiService._user_with_identity(session, 99)
    assert exc.value.status_code == 404
