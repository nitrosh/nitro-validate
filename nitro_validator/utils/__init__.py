"""
Utility functions and built-in rules for nitro-validator.
"""

from .rules import (
    # Basic rules
    RequiredRule,
    OptionalRule,
    # String rules
    AlphaRule,
    AlphanumericRule,
    EmailRule,
    UrlRule,
    RegexRule,
    # Numeric rules
    NumericRule,
    IntegerRule,
    MinRule,
    MaxRule,
    BetweenRule,
    # Comparison rules
    SameRule,
    DifferentRule,
    InRule,
    NotInRule,
    # Boolean rules
    BooleanRule,
    # Date rules
    DateRule,
    # Length rules
    LengthRule,
)

__all__ = [
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


def register_builtin_rules(registry):
    """
    Register all built-in validation rules with a registry.

    Args:
        registry: RuleRegistry instance to register rules with
    """
    rules = [
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
    ]

    for rule in rules:
        registry.register(rule)
