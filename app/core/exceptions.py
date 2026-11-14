from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """An error we raise on purpose. The handler below turns it into clean JSON."""

    status_code = 400
    code = "APP_ERROR"
    detail = "Something went wrong"
    headers: dict[str, str] | None = None

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail
        super().__init__(self.detail)


class PizzaNotFoundError(AppError):
    status_code = 404
    code = "PIZZA_NOT_FOUND"
    detail = "We don't have that pizza on the menu"


class OrderNotFoundError(AppError):
    status_code = 404
    code = "ORDER_NOT_FOUND"
    detail = "We can't find that order"


class PizzaInUseError(AppError):
    status_code = 409
    code = "PIZZA_IN_USE"
    detail = "That pizza has orders, so it has to stay on the menu"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"
    detail = "Only the chef can do that 👨‍🍳 Send the X-API-Key header"


class EmailTakenError(AppError):
    status_code = 409
    code = "EMAIL_TAKEN"
    detail = "That e-mail already has an account"


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    detail = "Wrong e-mail or password"


class NotAuthenticatedError(AppError):
    status_code = 401
    code = "NOT_AUTHENTICATED"
    detail = "Log in first, then send the access token as a Bearer token"
    headers = {"WWW-Authenticate": "Bearer"}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    content = {"detail": exc.detail, "code": exc.code}
    return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
