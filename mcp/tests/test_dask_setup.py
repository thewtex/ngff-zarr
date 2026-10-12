# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""A conversion's Dask setup lasts for that conversion only."""

import psutil
from ngff_zarr import config

from ngff_zarr_mcp.utils import setup_dask_config


def test_cache_dir_is_restored(tmp_path):
    """A cache_dir must not become every later call's cache."""
    before = config.cache_store

    with setup_dask_config(cache_dir=str(tmp_path / "cache")):
        assert config.cache_store == (tmp_path / "cache").resolve()

    assert config.cache_store == before


def test_local_cluster_has_a_worker_and_is_closed(monkeypatch):
    """One core gave zero workers, and the cluster outlived the call."""
    monkeypatch.setattr(psutil, "cpu_count", lambda logical=True: 1)

    with setup_dask_config(use_local_cluster=True) as client:
        cluster = client.cluster
        assert len(cluster.workers) == 1

    assert cluster.status.name == "closed"
