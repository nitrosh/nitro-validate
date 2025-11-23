"""
Custom exception classes for nitro-validator.
"""


class ValidatorException(Exception):
    """Base exception for all validator errors."""
    pass


class ValidationError(ValidatorException):
    """
    Raised when validation fails.

    Attributes:
        errors: Dictionary of field names to error messages
    """

    def __init__(self, errors):
        self.errors = errors
        super().__init__(f"Validation failed: {errors}")


class RuleNotFoundError(ValidatorException):
    """Raised when a validation rule is not found."""
    pass


class InvalidRuleError(ValidatorException):
    """Raised when a rule is invalid or improperly defined."""
    pass
