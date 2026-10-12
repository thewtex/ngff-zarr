# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""A running tool leaves the server's event loop free.

The tools do blocking work (reading, downsampling, writing). Run on the event
loop, one conversion stalls every other request, pings included.
"""

import asyncio
import time

import pytest

from ngff_zarr_mcp import server


@pytest.mark.asyncio
async def test_a_conversion_leaves_the_event_loop_free(monkeypatch):
    async def blocking_conversion(*args):
        time.sleep(0.3)
        return "converted"

    monkeypatch.setattr(server, "convert_to_ome_zarr", blocking_conversion)
    ticks = 0

    async def tick():
        nonlocal ticks
        while True:
            await asyncio.sleep(0.01)
            ticks += 1

    ticker = asyncio.create_task(tick())
    result = await server.convert_images_to_ome_zarr(["in.nrrd"], "out.ome.zarr")
    ticker.cancel()

    assert result == "converted"
    assert ticks >= 10
