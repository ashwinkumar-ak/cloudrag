from backend.repositories.documents import DocumentRepository


def main():
    repository = DocumentRepository()

    document_id = repository.create_document(
        filename="repository-test.txt",
        content_type="text/plain",
        file_size=123,
    )

    print(f"Created document: {document_id}")

    document = repository.get_document(document_id)

    print(f"Retrieved document: {document}")


if __name__ == "__main__":
    main()