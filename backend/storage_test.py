from pathlib import Path

from backend.config import settings
from backend.storage import DocumentStorage


def main():
    original_backend = settings.storage_backend
    original_path = settings.local_storage_path

    try:
        settings.storage_backend = "local"
        settings.local_storage_path = "./storage-test"

        storage = DocumentStorage()
        path = "users/1/storage-test.txt"
        content = b"CloudRAG storage test"

        storage.upload(
            path=path,
            content=content,
            content_type="text/plain",
        )

        assert storage.download(path) == content

        storage.delete(path)

        assert not (
            Path(settings.local_storage_path) / path
        ).exists()

        print("Storage test passed.")

    finally:
        settings.storage_backend = original_backend
        settings.local_storage_path = original_path


if __name__ == "__main__":
    main()
