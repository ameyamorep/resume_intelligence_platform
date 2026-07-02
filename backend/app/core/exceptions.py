class DomainError(Exception):
    """Base class for errors the API maps to HTTP responses."""

    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class UnsupportedFileType(DomainError):
    status_code = 415


class DocumentParseError(DomainError):
    status_code = 422


class EmptyDocumentError(DomainError):
    status_code = 422


class NotFoundError(DomainError):
    status_code = 404
