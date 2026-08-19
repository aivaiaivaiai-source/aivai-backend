"""Domain and infrastructure exceptions with HTTP-friendly metadata."""


class AppException(Exception):
    """Base exception for application-level errors."""

    default_status_code = 500
    default_code = "APP_ERROR"

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        code: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        self.message = message or ""
        self.status_code = (
            status_code if status_code is not None else self.default_status_code
        )
        self.code = code
        self.extra = extra or {}
        super().__init__(self.message)

    @property
    def error_code(self) -> str:
        return self.code or self.default_code


class EntityNotFoundError(AppException):
    """Raised when a referenced entity does not exist."""

    default_status_code = 404
    default_code = "ENTITY_NOT_FOUND"

    def __init__(
        self,
        entity_name: str,
        *,
        entity_id: str | int | None = None,
        message: str | None = None,
    ) -> None:
        if message is not None:
            super().__init__(message)
            return
        if entity_id is not None:
            super().__init__(f"{entity_name} with id={entity_id} not found")
        else:
            super().__init__(f"{entity_name} not found")


class TransactionFailedError(AppException):
    """Raised when commit or flush fails after rollback."""

    default_status_code = 503
    default_code = "TRANSACTION_FAILED"


class OwnershipError(AppException):
    """Raised when an operation is not allowed for the current principal."""

    default_status_code = 403
    default_code = "OWNERSHIP_ERROR"


class UnauthorizedError(AppException):
    """Raised when authentication fails or credentials are invalid."""

    default_status_code = 401
    default_code = "UNAUTHORIZED"


class RateLimitExceededError(AppException):
    """Too many requests for the caller (time-window limit)."""

    default_status_code = 429
    default_code = "RATE_LIMIT_EXCEEDED"


class InsufficientBalanceError(AppException):
    """Wallet cannot cover a charge. Client should offer top-up."""

    default_status_code = 402
    default_code = "TOPUP_REQUIRED"

    def __init__(
        self,
        *,
        balance: object,
        required_amount: object,
        shortfall: object,
    ) -> None:
        super().__init__(
            f"Недостаточно средств. Нужно {required_amount} сом, на балансе {balance}.",
            extra={
                "balance": str(balance),
                "required_amount": str(required_amount),
                "shortfall": str(shortfall),
            },
        )
