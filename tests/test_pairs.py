"""Testing generating image pairs paths."""

from math import comb
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from dual_choice.pairs_logic import generate_image_pairs, get_image_paths


@pytest.fixture
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


def test_generate_image_pairs(setup_test_directory):
    data_directory = setup_test_directory
    pairs = generate_image_pairs(str(data_directory))

    total_combinations = 0
    for folder in Path(data_directory).iterdir():
        if folder.is_dir():
            num_images = len(list(folder.iterdir()))
            total_combinations += comb(num_images, 2)

    assert len(pairs) > 0
    for folder, img1, img2 in pairs:
        folder, img1, img2 = map(lambda x: Path(x), (folder, img1, img2))
        assert folder.is_dir()
        assert img1.is_file()
        assert img2.is_file()
        assert img1.parent == folder
        assert img2.parent == folder
    assert len(pairs) == total_combinations


def test_get_image_paths(setup_test_directory):
    data_directory = setup_test_directory
    pairs = generate_image_pairs(str(data_directory))
    for pair in pairs:
        image_paths = get_image_paths(pair)
        image_paths = list(map(lambda x: Path(x), image_paths))
        assert len(image_paths) == 2
        assert all(path.is_file() for path in image_paths)
        # check if it has parent folder
        assert image_paths[0].parent == image_paths[1].parent
        assert image_paths[0].name != image_paths[1].name
        assert all(str(i).endswith("jpg") for i in image_paths)
