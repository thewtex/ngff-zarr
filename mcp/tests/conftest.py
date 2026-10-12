# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""Test configuration for pytest."""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_input_file():
    """Path to the test input file."""
    return Path(__file__).parent.parent / "test" / "data" / "input" / "MR-head.nrrd"


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)
