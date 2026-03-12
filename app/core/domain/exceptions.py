class AppError(Exception):
    message = "Application error"

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppError):
    message = "Entity not found"


class ValidationError(AppError):
    message = "Validation error"


class ConflictError(AppError):
    message = "Conflict error"


class ExternalServiceError(AppError):
    message = "External service error"