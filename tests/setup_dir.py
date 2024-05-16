"""Setup directory for generating image pairs from it."""

import pytest


from pathlib import Path
from tempfile import TemporaryDirectory


@pytest.fixture(scope="function")
def setup_test_directory():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        folder1 = temp_path / "1"
        folder1.mkdir()
        (folder1 / "0.jpg").touch()
        (folder1 / "1.jpg").touch()
        (folder1 / "2.jpg").touch()

        folder2 = temp_path / "2"
        folder2.mkdir()
        (folder2 / "0.jpg").touch()
        (folder2 / "1.jpg").touch()

        yield temp_path
