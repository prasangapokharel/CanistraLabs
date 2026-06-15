"""Tests for dfx lifecycle helpers."""

from unittest.mock import patch

from app.services.dfxLifecycle import ensure_local_replica, is_local_replica_running


class TestRequireLocalReplica:
    @patch("app.services.dfxLifecycle._wait_for_local_replica", return_value=True)
    @patch("app.services.dfxLifecycle.ensure_local_replica")
    @patch("app.services.dfxLifecycle.is_local_replica_running")
    def test_require_succeeds_when_running(self, mock_ping, mock_ensure, _mock_wait):
        mock_ping.return_value = True
        from app.services.dfxLifecycle import require_local_replica

        require_local_replica()  # no raise
        mock_ensure.assert_not_called()

    @patch("app.services.dfxLifecycle._wait_for_local_replica", return_value=False)
    @patch("app.services.dfxLifecycle.ensure_local_replica", return_value={"running": False})
    @patch("app.services.dfxLifecycle.is_local_replica_running", return_value=False)
    def test_require_raises_when_down(self, _mock_ping, _mock_ensure, _mock_wait):
        from app.services.dfxLifecycle import require_local_replica

        try:
            require_local_replica()
            assert False, "expected RuntimeError"
        except RuntimeError as exc:
            assert "dfx replica" in str(exc).lower()


class TestDfxLifecycle:
    @patch("app.services.dfxLifecycle.subprocess.run")
    def test_ping_success(self, mock_run):
        mock_run.return_value.returncode = 0
        assert is_local_replica_running() is True

    @patch("app.services.dfxLifecycle._wait_for_local_replica", return_value=True)
    @patch("app.services.dfxLifecycle._start_replica", return_value=(0, "", ""))
    @patch("app.services.dfxLifecycle._dfx_killall")
    @patch("app.services.dfxLifecycle.settings")
    @patch("app.services.dfxLifecycle.is_local_replica_running")
    @patch("app.services.dfxLifecycle.shutil.which")
    def test_ensure_starts_when_down(
        self, mock_which, mock_ping, mock_settings, _mock_kill, mock_start, _mock_wait
    ):
        mock_settings.dfx_auto_start = True
        mock_settings.dfx_path = "/usr/bin/dfx"
        mock_which.return_value = "/usr/bin/dfx"
        mock_ping.side_effect = [False, True]

        result = ensure_local_replica()

        assert result["running"] is True
        assert result["action"] == "started"
        mock_start.assert_called_once_with(clean=False)

    @patch("app.services.dfxLifecycle._wait_for_local_replica")
    @patch("app.services.dfxLifecycle._start_replica")
    @patch("app.services.dfxLifecycle._dfx_killall")
    @patch("app.services.dfxLifecycle.settings")
    @patch("app.services.dfxLifecycle.is_local_replica_running")
    @patch("app.services.dfxLifecycle.shutil.which")
    def test_ensure_retries_clean_on_pocketic_error(
        self, mock_which, mock_ping, mock_settings, _mock_kill, mock_start, mock_wait
    ):
        mock_settings.dfx_auto_start = True
        mock_settings.dfx_path = "/usr/bin/dfx"
        mock_which.return_value = "/usr/bin/dfx"
        mock_ping.side_effect = [False, False, False, True]
        mock_start.side_effect = [
            (1, "", "ERROR: Failed to initialize PocketIC: HTTP 400 Bad Request for /instances"),
            (0, "Replica API running", ""),
        ]
        mock_wait.side_effect = [False, True]

        result = ensure_local_replica()

        assert result["running"] is True
        assert result["action"] == "started_clean"
        assert mock_start.call_count == 2
        mock_start.assert_any_call(clean=False)
        mock_start.assert_any_call(clean=True)

    @patch("app.services.dfxLifecycle.settings")
    @patch("app.services.dfxLifecycle.is_local_replica_running")
    def test_ensure_skips_when_disabled(self, mock_ping, mock_settings):
        mock_settings.dfx_auto_start = False
        mock_ping.return_value = False

        result = ensure_local_replica()

        assert result["action"] == "disabled"
        assert result["running"] is False
