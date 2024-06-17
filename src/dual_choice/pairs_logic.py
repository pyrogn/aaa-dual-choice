import random
from itertools import combinations
from pathlib import Path


def generate_image_pairs(data_directory: str) -> list[tuple[str, str, str]]:
    """
    Создать пары изображений формата
        [папка абс., отн. путь в папке до изобр. 1, ...до изобр 2]
    например ['/data/232', '2.jpg', '0.jpg']
    """
    data_path = Path(data_directory)
    folders = [folder for folder in data_path.iterdir() if folder.is_dir()]
    pairs = []
    random.shuffle(folders)

    for folder in folders:
        images = [i.name for i in folder.iterdir() if i.is_file()]
        image_combinations = list(combinations(images, 2))
        random.shuffle(image_combinations)
        for comb in image_combinations:
            pairs.append((str(folder), comb[0], comb[1]))
    random.shuffle(pairs)
    return pairs


def count_image_pairs(data_directory: str) -> int:
    data_path = Path(data_directory)
    folders = [folder for folder in data_path.iterdir() if folder.is_dir()]
    total_pairs = 0

    for folder in folders:
        images = [i.name for i in folder.iterdir() if i.is_file()]
        total_pairs += len(list(combinations(images, 2)))

    return total_pairs


def get_image_paths(pair) -> tuple[str, str]:
    """
    Из пары формата выше получить два корретных пути для пары фото
    К примеру ['/data/232/3.jpg', '/data/232/0.jpg']
    """
    folder, image1, image2 = pair
    images = [str(Path(folder) / image) for image in (image1, image2)]
    return tuple(images)  # type: ignore
