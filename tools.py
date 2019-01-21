import os

def is_file_exists(path: str) -> bool:
    return os.path.exists(path)

def create_folder(path: str):
    if not is_file_exists(path):
        os.makedirs(path)
