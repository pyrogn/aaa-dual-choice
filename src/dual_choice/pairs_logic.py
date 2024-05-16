import random
from itertools import combinations
from pathlib import Path


def generate_image_pairs(data_directory: str) -> list[tuple[str, str, str]]:
    """
    Generate unique image pairs from the specified data directory.

    Args:
        data_directory (str): Path to the directory containing image folders.

    Returns:
        List[Tuple[Path, Path, Path]]: A list of tuples, each containing
        a folder path and two image paths.
    """
    data_path = Path(data_directory)
    folders = [folder for folder in data_path.iterdir() if folder.is_dir()]
    pairs = []
    random.shuffle(folders)

    for folder in folders:
        images = list(folder.iterdir())
        image_combinations = list(combinations(images, 2))
        random.shuffle(image_combinations)
        for comb in image_combinations:
            pairs.append((str(folder), *list(map(str, comb))))
    random.shuffle(pairs)
    return pairs


def get_image_paths(pair) -> tuple[str, str]:
    """
    Given a tuple containing folder and image paths, return a list
    of the two image paths in random order.

    Args:
        pair (Tuple[Path, Path, Path]): A tuple containing a folder path
        and two image paths.

    Returns:
        List[Path]: A list containing the two image paths in random order.
    """
    folder, image1, image2 = pair
    images = [str(Path(folder) / image) for image in (image1, image2)]
    return tuple(images)  # type: ignore
