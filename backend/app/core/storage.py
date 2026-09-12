"""Storage abstraction layer supporting Local and future Object Storage backends."""

import os
import shutil
import uuid
from abc import ABC, abstractmethod
from typing import BinaryIO

from app.config.settings import get_settings
from app.core.exceptions import ValidationException

settings = get_settings()


class StorageBackend(ABC):
    """Abstract interface for dataset and model artifact storage."""

    @abstractmethod
    def save_file(self, file_obj: BinaryIO, filename: str, subfolder: str = "uploads") -> str:
        """Save file and return its canonical storage path."""
        pass

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Delete file at specified storage path."""
        pass

    @abstractmethod
    def get_absolute_path(self, storage_path: str) -> str:
        """Return safe, validated local filesystem path."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage implementation with strict path traversal protection."""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _sanitize_path(self, relative_path: str) -> str:
        """Ensure path remains within self.base_dir to prevent path traversal attacks."""
        target_path = os.path.abspath(os.path.join(self.base_dir, relative_path))
        if not target_path.startswith(self.base_dir):
            raise ValidationException("Path traversal attempt detected")
        return target_path

    def save_file(self, file_obj: BinaryIO, filename: str, subfolder: str = "uploads") -> str:
        safe_subfolder = os.path.join(self.base_dir, subfolder)
        os.makedirs(safe_subfolder, exist_ok=True)

        file_ext = os.path.splitext(filename)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        destination = os.path.join(safe_subfolder, unique_filename)

        with open(destination, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)

        # Return relative storage path for portability
        return os.path.relpath(destination, start=self.base_dir).replace("\\", "/")

    def delete_file(self, storage_path: str) -> bool:
        try:
            full_path = self._sanitize_path(storage_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception:
            return False

    def get_absolute_path(self, storage_path: str) -> str:
        return self._sanitize_path(storage_path)


# Default storage singleton
storage_backend: StorageBackend = LocalStorageBackend(base_dir="data")
