"""Domain errors for Result[T, DomainError] flows."""

from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    NOT_FOUND = "not_found"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_API = "external_api"
    PERSISTENCE = "persistence"
    POLICY = "policy"


@dataclass(frozen=True, slots=True)
class DomainError:
    code: ErrorCode
    message: str
    details: dict[str, str] | None = None
