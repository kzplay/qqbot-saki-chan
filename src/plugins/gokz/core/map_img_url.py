from pathlib import Path


def get_map_img_url(map_name) -> Path:
    return Path(f"data/map-images-master/images/{map_name}.jpg")
