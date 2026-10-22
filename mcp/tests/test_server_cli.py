# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""The server's command line."""

import sys

import pytest

from ngff_zarr_mcp import server


@pytest.fixture
def run_main(monkeypatch):
    """Run main() with *args*, without serving, on a copy of the settings."""
    monkeypatch.setattr(server.mcp, "settings", server.mcp.settings.model_copy())
    monkeypatch.setattr(server.mcp, "run", lambda **kwargs: None)

    def run(*args):
        monkeypatch.setattr(sys, "argv", ["ngff-zarr-mcp", *args])
        server.main()
        return server.mcp.settings

    return run


def test_a_public_host_accepts_requests_for_its_names(run_main):
    """FastMCP limits Host headers to localhost for its default host.

    With --host 0.0.0.0 every client that used the server's own name got
    421 Invalid Host header.
    """
    settings = run_main("--transport", "streamable-http", "--host", "0.0.0.0")

    assert settings.transport_security is None


def test_localhost_keeps_its_dns_rebinding_protection(run_main):
    settings = run_main("--transport", "streamable-http", "--host", "localhost")

    assert settings.transport_security.enable_dns_rebinding_protection
