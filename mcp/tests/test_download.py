# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""Downloading an input URL the agent passed."""

import httpx
import pytest

from ngff_zarr_mcp import utils

# A documentation address (TEST-NET-1): routable, and resolving it needs no DNS.
REMOTE = "http://192.0.2.1"


@pytest.fixture
def served(monkeypatch):
    """Serve `/image.nrrd` and redirects to it, without a network."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/image.nrrd"):
            return httpx.Response(200, content=b"image bytes")
        return httpx.Response(302, headers={"Location": request.url.params["to"]})

    real_client = httpx.AsyncClient

    def client(**kwargs):
        return real_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(utils.httpx, "AsyncClient", client)


@pytest.mark.asyncio
async def test_follows_a_redirect(served, tmp_path):
    destination = tmp_path / "image.nrrd"

    await utils.download_file(
        f"{REMOTE}/record?to={REMOTE}/files/image.nrrd", destination
    )

    assert destination.read_bytes() == b"image bytes"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/image.nrrd",
        "http://[::1]/image.nrrd",
        # The unspecified address reaches a listener bound to all interfaces.
        "http://0.0.0.0/image.nrrd",
        "http://[::]/image.nrrd",
        "http://[::ffff:127.0.0.1]/image.nrrd",
        # A cloud metadata endpoint, reached through a redirect.
        f"{REMOTE}/record?to=http://169.254.169.254/image.nrrd",
    ],
)
async def test_refuses_a_local_host(served, tmp_path, url):
    destination = tmp_path / "image.nrrd"

    with pytest.raises(ValueError, match="local address"):
        await utils.download_file(url, destination)

    assert not destination.exists()


@pytest.mark.asyncio
async def test_refuses_two_inputs_with_one_name(served, tmp_path):
    """The second download would replace the first."""
    urls = [f"{REMOTE}/a/image.nrrd", f"{REMOTE}/b/image.nrrd"]

    with pytest.raises(ValueError, match="image.nrrd"):
        await utils.prepare_input_files(urls, str(tmp_path))
