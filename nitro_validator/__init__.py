"""
Nitro Validator - A powerful, standalone, dependency-free data validation library.

Example:
    from nitro_validator import NitroValidator

    data = {'email': 'user@example.com', 'age': 25}
    rules = {'email': 'required|email', 'age': 'required|numeric|min:18'}

    validator = NitroValidator()
    validated = validator.validate(data, rules)
"""

__version__ = "1.0.4"

from typing import Optional

from .core import (
    NitroValidator,
    NitroValidationRule,
    NitroRuleRegistry,
    NitroValidationError,
    NitroValidatorException,
    NitroRuleNotFoundError,
    NitroInvalidRuleError,
)

from .utils import (
    RequiredRule,
    OptionalRule,
    AlphaRule,
    AlphanumericRule,
    EmailRule,
    UrlRule,
    RegexRule,
    LowercaseRule,
    UppercaseRule,
    AlphaDashRule,
    StartsWithRule,
    EndsWithRule,
    ContainsRule,
    UuidRule,
    IpRule,
    Ipv4Rule,
    Ipv6Rule,
    JsonRule,
    SlugRule,
    AsciiRule,
    Base64Rule,
    HexColorRule,
    CreditCardRule,
    MacAddressRule,
    TimezoneRule,
    LocaleRule,
    NumericRule,
    IntegerRule,
    MinRule,
    MaxRule,
    BetweenRule,
    PositiveRule,
    NegativeRule,
    DivisibleByRule,
    SameRule,
    DifferentRule,
    InRule,
    NotInRule,
    BooleanRule,
    DateRule,
    BeforeRule,
    AfterRule,
    DateEqualsRule,
    DateFormatRule,
    ConfirmedRule,
    AcceptedRule,
    DeclinedRule,
    LengthRule,
    ArrayRule,
    SizeRule,
    DistinctRule,
    register_builtin_rules,
)

# Auto-register built-in rules with default registry
_default_registry = NitroRuleRegistry()
register_builtin_rules(_default_registry)

# Override NitroValidator to use the default registry with built-in rules
_OriginalNitroValidator = NitroValidator


class NitroValidator(_OriginalNitroValidator):
    """Validate data against rules, with every built-in rule pre-registered.

    This is the public entry point exported at the top level of the
    package. It is a thin subclass of
    :class:`nitro_validator.core.NitroValidator` whose only job is to
    default the registry to a fresh copy of the module-level registry,
    which is pre-populated with all 51+ built-in rules. Each
    ``NitroValidator()`` therefore gets its own registry, so
    ``register_rule()`` calls are isolated to that instance. Pass
    ``registry=`` to supply your own.

    Example:
        >>> from nitro_validator import NitroValidator
        >>> v = NitroValidator()
        >>> v.validate(
        ...     {'email': 'a@b.co', 'age': 21},
        ...     {'email': 'required|email', 'age': 'required|integer|min:18'},
        ... )
        {'email': 'a@b.co', 'age': 21}
    """

    def __init__(self, registry: Optional["NitroRuleRegistry"] = None):
        """Create a validator, defaulting to a fresh copy of the built-in registry.

        Args:
            registry: A custom :class:`NitroRuleRegistry`. Omit to get a
                fresh registry seeded with every built-in rule; rules
                you register on this validator will not leak to others.
        """
        super().__init__(registry if registry is not None else _default_registry.copy())


# Provide convenient aliases without "Nitro" prefix
Validator = NitroValidator
Rule = NitroValidationRule
RuleRegistry = NitroRuleRegistry
ValidationError = NitroValidationError
ValidatorException = NitroValidatorException
RuleNotFoundError = NitroRuleNotFoundError
InvalidRuleError = NitroInvalidRuleError


__all__ = [
    "__version__",
    # Nitro-prefixed classes (primary)
    "NitroValidator",
    "NitroValidationRule",
    "NitroRuleRegistry",
    "NitroValidationError",
    "NitroValidatorException",
    "NitroRuleNotFoundError",
    "NitroInvalidRuleError",
    # Convenient aliases (backward compatibility)
    "Validator",
    "Rule",
    "RuleRegistry",
    "ValidationError",
    "ValidatorException",
    "RuleNotFoundError",
    "InvalidRuleError",
    # Built-in rules
    "RequiredRule",
    "OptionalRule",
    "AlphaRule",
    "AlphanumericRule",
    "EmailRule",
    "UrlRule",
    "RegexRule",
    "LowercaseRule",
    "UppercaseRule",
    "AlphaDashRule",
    "StartsWithRule",
    "EndsWithRule",
    "ContainsRule",
    "UuidRule",
    "IpRule",
    "Ipv4Rule",
    "Ipv6Rule",
    "JsonRule",
    "SlugRule",
    "AsciiRule",
    "Base64Rule",
    "HexColorRule",
    "CreditCardRule",
    "MacAddressRule",
    "TimezoneRule",
    "LocaleRule",
    "NumericRule",
    "IntegerRule",
    "MinRule",
    "MaxRule",
    "BetweenRule",
    "PositiveRule",
    "NegativeRule",
    "DivisibleByRule",
    "SameRule",
    "DifferentRule",
    "InRule",
    "NotInRule",
    "BooleanRule",
    "DateRule",
    "BeforeRule",
    "AfterRule",
    "DateEqualsRule",
    "DateFormatRule",
    "ConfirmedRule",
    "AcceptedRule",
    "DeclinedRule",
    "LengthRule",
    "ArrayRule",
    "SizeRule",
    "DistinctRule",
    "register_builtin_rules",
]
