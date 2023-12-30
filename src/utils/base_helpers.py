import functools
import os
import time

from fastapi import UploadFile, File

from pydantic import BaseModel
from sqlalchemy.orm import Relationship
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


def preparing_base_fields(columns: list, payload: BaseModel) -> dict:
    """Returns a list of base field names"""
    dump_obj = payload.model_dump()

    return {key: value for key, value in dump_obj.items() if key in columns}


def get_related_and_base_columns(inspect_table) -> tuple:
    """Returns foreign keys and local columns"""
    related_columns: list[Relationship] = [
        _column.key for _column in inspect_table.relationships
    ]
    basic_columns = inspect_table.columns
    return related_columns, basic_columns


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
    def inner(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            file_name: str = kwargs.get("file").filename
            if file_name.split(".")[-1] not in content_types:
                raise InvalidContentType(content_types=content_types)
            return await func(*args, **kwargs)

        return wrapped

    return inner