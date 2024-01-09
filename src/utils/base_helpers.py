from __future__ import annotations

import functools
import os
import time

from fastapi import File
from fastapi import UploadFile

from slugify import slugify

from src.core.configs import settings, MB_TO_BYTES
from src.exceptions.base_exceptions import FileIsTooLarge, InvalidContentType


def validate_file(file: UploadFile = File(default=None)) -> UploadFile | None:
    """Validates file size, format"""

    size = settings.max_upload_file_size / MB_TO_BYTES
    if not file:
        return None
    if (file.size / MB_TO_BYTES) > size:
        raise FileIsTooLarge(size=size)

    return file


def get_file_path(
    direction: str,
    filename: str,
    old_path: str | None,
    file: UploadFile | None = None,
) -> str | None:
    """Generates and returns new file path,
    before doing path generation at first will be checked old path property, if it found so will be deleted,
    and will be created a new path for particular object
    """

    if old_path and os.path.isfile(old_path):
        os.remove(old_path)

    if not os.path.isdir(f"{settings.file_path}/{direction}/"):
        os.mkdir(f"{settings.file_path}/{direction}/")

    if not file:
        return None
    else:
        with open(
            f"{settings.file_path}/{direction}/{filename}.webp",
            "wb",
        ) as photo:
            photo.write(file.file.read())

        return photo.name


def generate_filename(file_prefix: str) -> str:
    return slugify(f"{file_prefix}_{int(time.time())}")


def check_content_type(content_types: list):
    """Content-Type checker decorator"""

    def inner(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            file_name: str = kwargs.get("file").filename
            if file_name.split(".")[-1] not in content_types:
                raise InvalidContentType(content_types=content_types)
            return await func(*args, **kwargs)

        return wrapped

    return inner
