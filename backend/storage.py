import os
import re
from pathlib import Path
from urllib.parse import quote

import requests

from backend.config import settings


class StorageError(RuntimeError):
    """Raised when document storage cannot complete an operation."""


class DocumentStorage:
    def __init__(self):
        self.backend = settings.storage_backend.lower()
        self.bucket = settings.supabase_storage_bucket

        if self.backend not in {"local", "supabase"}:
            raise StorageError(
                "STORAGE_BACKEND must be either 'local' or 'supabase'."
            )

        if self.backend == "supabase":
            if not settings.supabase_url:
                raise StorageError("SUPABASE_URL is not configured.")

            if not settings.supabase_service_role_key:
                raise StorageError(
                    "SUPABASE_SERVICE_ROLE_KEY is not configured."
                )

            if not self.bucket:
                raise StorageError(
                    "SUPABASE_STORAGE_BUCKET is not configured."
                )

    def build_path(self, user_id: int, filename: str) -> str:
        safe_name = Path(filename).name
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", safe_name).strip("._")

        if not safe_name:
            safe_name = "document"

        # A UUID-like random component is supplied by the caller through
        # build_unique_path, keeping storage paths collision-resistant.
        return f"users/{user_id}/{safe_name}"

    def upload(
        self,
        path: str,
        content: bytes,
        content_type: str,
    ) -> None:
        if self.backend == "local":
            self._upload_local(path, content)
            return

        self._upload_supabase(path, content, content_type)

    def delete(self, path: str) -> None:
        if not path:
            return

        if self.backend == "local":
            self._delete_local(path)
            return

        self._delete_supabase(path)

    def download(self, path: str) -> bytes:
        if not path:
            raise StorageError("Document storage path is missing.")

        if self.backend == "local":
            return self._download_local(path)

        return self._download_supabase(path)

    def _upload_local(self, path: str, content: bytes) -> None:
        root = Path(settings.local_storage_path).resolve()
        target = (root / path).resolve()

        if root not in target.parents:
            raise StorageError("Invalid local storage path.")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def _delete_local(self, path: str) -> None:
        root = Path(settings.local_storage_path).resolve()
        target = (root / path).resolve()

        if root not in target.parents:
            raise StorageError("Invalid local storage path.")

        try:
            target.unlink()
        except FileNotFoundError:
            return

    def _download_local(self, path: str) -> bytes:
        root = Path(settings.local_storage_path).resolve()
        target = (root / path).resolve()

        if root not in target.parents:
            raise StorageError("Invalid local storage path.")

        try:
            return target.read_bytes()
        except FileNotFoundError as exc:
            raise StorageError("Stored document file was not found.") from exc

    def _supabase_headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {
            "Authorization": (
                f"Bearer {settings.supabase_service_role_key}"
            ),
            "apikey": settings.supabase_service_role_key,
        }

        if content_type:
            headers["Content-Type"] = content_type

        return headers

    def _supabase_object_url(self, path: str) -> str:
        encoded_path = quote(path, safe="/")
        return (
            f"{settings.supabase_url.rstrip('/')}"
            f"/storage/v1/object/{quote(self.bucket, safe='')}"
            f"/{encoded_path}"
        )

    def _upload_supabase(
        self,
        path: str,
        content: bytes,
        content_type: str,
    ) -> None:
        try:
            response = requests.post(
                self._supabase_object_url(path),
                headers={
                    **self._supabase_headers(content_type),
                    "x-upsert": "false",
                },
                data=content,
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            detail = "Supabase Storage upload failed."

            if exc.response is not None:
                try:
                    payload = exc.response.json()
                    message = payload.get("message") or payload.get("error")
                    if message:
                        detail = f"Supabase Storage upload failed: {message}"
                except ValueError:
                    pass

            raise StorageError(detail) from exc

    def _delete_supabase(self, path: str) -> None:
        try:
            response = requests.delete(
                self._supabase_object_url(path),
                headers=self._supabase_headers(),
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise StorageError(
                "Supabase Storage deletion failed."
            ) from exc

    def _download_supabase(self, path: str) -> bytes:
        try:
            response = requests.get(
                self._supabase_object_url(path),
                headers=self._supabase_headers(),
                timeout=60,
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            raise StorageError(
                "Supabase Storage download failed."
            ) from exc
