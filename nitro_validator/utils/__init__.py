"""
Utility functions and built-in rules for nitro-validator.
"""

from ..core.rule_registry import NitroRuleRegistry

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
    # Numeric rules
    NumericRule,
    IntegerRule,
    MinRule,
    MaxRule,
    BetweenRule,
    PositiveRule,
    NegativeRule,
    DivisibleByRule,
    # Comparison rules
    SameRule,
    DifferentRule,
    InRule,
    NotInRule,
    # Boolean rules
    BooleanRule,
    # Date rules
    DateRule,
    BeforeRule,
    AfterRule,
    DateEqualsRule,
    DateFormatRule,
    # Convenience rules
    ConfirmedRule,
    AcceptedRule,
    DeclinedRule,
    # Length rules
    LengthRule,
    # Collection rules
    ArrayRule,
    SizeRule,
    DistinctRule,
)

__all__ = [
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


def register_builtin_rules(registry: NitroRuleRegistry) -> None:
    """Register every built-in validation rule onto ``registry``.

    The default registry returned by :class:`NitroValidator()
    <nitro_validator.NitroValidator>` is already populated with these
    rules — call this only when you are building a custom registry
    from scratch and want the built-ins available under their standard
    names.

    Args:
        registry: A :class:`NitroRuleRegistry` instance to mutate.

    Example:
        >>> from nitro_validator import NitroRuleRegistry, register_builtin_rules
        >>> registry = NitroRuleRegistry()
        >>> register_builtin_rules(registry)
        >>> registry.has("email")
        True
    """
    rules = [
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
    ]

    for rule in rules:
        registry.register(rule)
