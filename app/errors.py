class AppError(Exception):
    """A business-rule failure the API turns into a 4xx with {"error": message}."""
    status = 400
    message = "Bad request"

    def __init__(self, message=None):
        super().__init__(message or self.message)
        self.message = message or self.message


class NotFound(AppError):
    status = 404
    message = "Not found"


class NotAllowed(AppError):
    status = 403
    message = "You are not allowed to do that"


class SoldOut(AppError):
    status = 409
    message = "This event is sold out"


class AlreadyHolds(AppError):
    status = 409
    message = "You already hold a ticket for this event"


class EventStarted(AppError):
    status = 409
    message = "This event has already started"


class Unauthorized(AppError):
    status = 401
    message = "Please log in"


class Invalid(AppError):
    status = 422
    message = "Invalid data"


class Conflict(AppError):
    status = 409
    message = "Conflict"
