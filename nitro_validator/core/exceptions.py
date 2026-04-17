"""
Custom exception classes for nitro-validator.
"""

from typing import Dict, List


class NitroValidatorException(Exception):
    """Base exception for every error raised by nitro-validator.

    Catch this when you want to trap anything the library throws without
    caring which specific failure occurred. All other exceptions in the
    package subclass this one.

    Example:
        >>> try:
        ...     validator.validate(data, rules)
        ... except NitroValidatorException:
        ...     # catches ValidationError, RuleNotFoundError, InvalidRuleError
        ...     pass
    """

    pass


class NitroValidationError(NitroValidatorException):
    """Raise when one or more fields fail validation.

    The `errors` attribute maps each failing field name to a list of
    human-readable error messages. Rules that pass do not appear. This is
    the exception raised by :meth:`NitroValidator.validate` on failure.

    Attributes:
        errors: Dict mapping field name to a list of error messages for
            that field.

    Example:
        >>> try:
        ...     validator.validate({'email': ''}, {'email': 'required|email'})
        ... except NitroValidationError as e:
        ...     print(e.errors)
        {'email': ['The email field is required.']}
    """

    def __init__(self, errors: Dict[str, List[str]]):
        """Build the exception with a field-keyed error map.

        Args:
            errors: Dict of field name to list of error strings.
        """
        self.errors = errors
        super().__init__(f"Validation failed: {errors}")


class NitroRuleNotFoundError(NitroValidatorException):
    """Raise when a rule name is referenced but has not been registered.

    Typically surfaced when a rule string like ``'my_custom_rule'`` is
    used before the corresponding rule class is registered on the
    validator's registry.

    Example:
        >>> validator.validate({'x': 1}, {'x': 'not_a_real_rule'})
        Traceback (most recent call last):
            ...
        NitroRuleNotFoundError: Rule 'not_a_real_rule' not found in registry
    """

    pass


class NitroInvalidRuleError(NitroValidatorException):
    """Raise when a rule class is malformed or fails registration checks.

    Thrown by :meth:`NitroRuleRegistry.register` when the supplied class
    does not inherit from :class:`NitroValidationRule` or lacks a usable
    ``name`` attribute.
    """

    pass
