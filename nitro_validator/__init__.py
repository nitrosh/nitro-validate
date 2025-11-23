"""
Nitro Validator - A powerful, standalone, dependency-free data validation library.

Example:
    from nitro_validator import Validator

    data = {'email': 'user@example.com', 'age': 25}
    rules = {'email': 'required|email', 'age': 'required|numeric|min:18'}

    validator = Validator()
    validated = validator.validate(data, rules)
"""

__version__ = "1.0.0"

from .core import (
    Validator,
    Rule,
    RuleRegistry,
    ValidationError,
    ValidatorException,
    RuleNotFoundError,
    InvalidRuleError,
)

from .utils import (
    RequiredRule,
    OptionalRule,
    AlphaRule,
    AlphanumericRule,
    EmailRule,
    UrlRule,
    RegexRule,
    NumericRule,
    IntegerRule,
    MinRule,
    MaxRule,
    BetweenRule,
    SameRule,
    DifferentRule,
    InRule,
    NotInRule,
    BooleanRule,
    DateRule,
    LengthRule,
    register_builtin_rules,
)

# Auto-register built-in rules with default registry
_default_registry = RuleRegistry()
register_builtin_rules(_default_registry)

# Override Validator to use the default registry with built-in rules
_OriginalValidator = Validator


class Validator(_OriginalValidator):
    """
    Validator with built-in rules pre-registered.
    """

    def __init__(self, registry=None):
        super().__init__(registry or _default_registry)


__all__ = [
    '__version__',
    'Validator',
    'Rule',
    'RuleRegistry',
    'ValidationError',
    'ValidatorException',
    'RuleNotFoundError',
    'InvalidRuleError',
    'RequiredRule',
    'OptionalRule',
    'AlphaRule',
    'AlphanumericRule',
    'EmailRule',
    'UrlRule',
    'RegexRule',
    'NumericRule',
    'IntegerRule',
    'MinRule',
    'MaxRule',
    'BetweenRule',
    'SameRule',
    'DifferentRule',
    'InRule',
    'NotInRule',
    'BooleanRule',
    'DateRule',
    'LengthRule',
    'register_builtin_rules',
]
