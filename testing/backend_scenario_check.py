#!/usr/bin/env python3
"""Live API scenario checks against running backend."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
EMAIL = "demo@example.com"
PASSWORD = "demopass123"


def req(method: str, path: str, token: str | None = None, body: dict | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return e.code, payload


def ok(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    return passed


def main() -> int:
    results: list[bool] = []

    code, data = req("POST", "/api/v1/auth/login", body={"email": EMAIL, "password": PASSWORD})
    token = data.get("access_token") if code == 200 else None
    results.append(ok("auth login", code == 200 and bool(token), f"status={code}"))

    code, data = req("POST", "/api/v1/auth/login", body={"email": EMAIL, "password": "wrong"})
    results.append(ok("auth bad password → 401", code == 401))

    code, data = req("GET", "/api/v1/wallet/identity", token=token)
    results.append(ok("wallet identity", code == 200, data.get("message", "")[:80]))
    results.append(
        ok(
            "wallet has requirements",
            code == 200 and isinstance(data.get("requirements"), dict),
        )
    )

    code, data = req("GET", "/api/v1/projects/", token=token)
    projects = data if isinstance(data, list) else data.get("data", data)
    if isinstance(projects, dict):
        projects = projects.get("items", [])
    results.append(ok("list projects", code == 200 and isinstance(projects, list)))

    # Deploy underfunded → pending_funding with structured fields
    code, data = req(
        "POST",
        f"/api/v1/dfx/projects/1/deploy",
        token=token,
        body={"code_content": "<html><body>scenario test</body></html>"},
    )
    results.append(ok("deploy returns 202", code == 202))
    results.append(
        ok(
            "deploy pending_funding structured",
            data.get("status") == "pending_funding" and data.get("error_code") == "insufficient_cycles",
            data.get("message", "")[:100],
        )
    )

    # Canister power on local-id project (project 6 = umwsh / m74gv...)
    code, data = req(
        "POST",
        f"/api/v1/dfx/projects/6/power",
        token=token,
        body={"enabled": False},
    )
    if code in (200, 404, 502, 503):
        detail = data.get("detail")
        msg = detail.get("message") if isinstance(detail, dict) else str(detail)
        results.append(
            ok(
                "canister power returns structured error or success",
                isinstance(detail, dict) or code == 200,
                f"status={code} {str(msg)[:90]}",
            )
        )
    else:
        results.append(ok("canister power", False, f"unexpected status={code}"))

    # Metrics
    code, data = req("GET", "/api/v1/metrics/projects/1", token=token)
    results.append(ok("project metrics", code in (200, 404)))

    # Unauthorized
    code, _ = req("GET", "/api/v1/projects/")
    results.append(ok("projects without auth → 401", code == 401))

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} scenarios passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
