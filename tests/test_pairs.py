"""Testing generating image pairs paths."""

from math import comb
from pathlib import Path
from dual_choice.pairs_logic import generate_image_pairs, get_image_paths
from setup_dir import setup_test_directory  # noqa: F401


def test_generate_image_pairs(setup_test_directory):
    data_directory = str(setup_test_directory)
    pairs = generate_image_pairs(data_directory)

    total_combinations = 0
    for folder in Path(data_directory).iterdir():
        if folder.is_dir():
            num_images = len(list(folder.iterdir()))
            total_combinations += comb(num_images, 2)

    assert len(pairs) > 0
    assert len(pairs) == total_combinations

    for folder, img1, img2 in pairs:
        folder_path = Path(data_directory) / folder
        img1_path = folder_path / img1
        img2_path = folder_path / img2
        assert folder_path.is_dir()
        assert img1_path.is_file()
        assert img2_path.is_file()
        assert img1_path.parent == Path(folder)
        assert img2_path.parent == Path(folder)


def test_get_image_paths(setup_test_directory):
    data_directory = str(setup_test_directory)
    pairs = generate_image_pairs(data_directory)
    for pair in pairs:
        image_paths = get_image_paths(pair)
        image_paths = list(map(lambda x: Path(x), image_paths))
        assert len(image_paths) == 2
        assert all(path.is_file() for path in image_paths)
        # make sure they have the same parent
        assert image_paths[0].parent == image_paths[1].parent
        assert image_paths[0].name != image_paths[1].name
        assert all(str(i).endswith("jpg") for i in image_paths)
