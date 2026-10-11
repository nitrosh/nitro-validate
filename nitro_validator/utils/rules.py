"""
Built-in validation rules for nitro-validator.
"""

import copy
import functools
import ipaddress
import json as json_module
import math
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, FrozenSet, Optional, Tuple, Union
from ..core.exceptions import NitroInvalidRuleError
from ..core.rule import NitroValidationRule


Number = Union[int, float]

_INTEGER_PATTERN = re.compile(r"[+-]?[0-9]+")
_NUMBER_PATTERN = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def _to_number(value: Any) -> Optional[Number]:
    """Return ``value`` as a finite int or float, or None if it isn't one.

    Strings must be plain decimal or scientific notation. ``"nan"``,
    ``"inf"``, ``"1_000"``, padded strings, and booleans are rejected.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if not isinstance(value, str):
        return None
    if _INTEGER_PATTERN.fullmatch(value):
        try:
            return int(value)
        except ValueError:
            return None
    if _NUMBER_PATTERN.fullmatch(value):
        number = float(value)
        return number if math.isfinite(number) else None
    return None


def _number_arg(rule: NitroValidationRule, index: int) -> Number:
    """Return argument ``index`` of ``rule`` as a number, or raise."""
    number = _to_number(rule.args[index])
    if number is None:
        raise NitroInvalidRuleError(
            f"Rule '{rule.name}' expects a number for argument {index + 1}, "
            f"got {rule.args[index]!r}."
        )
    return number


_ISO_DATE_FORMATS: Tuple[str, ...] = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
)


def _parse_iso_date(date_value: Any) -> Optional[datetime]:
    """Parse a date, datetime or unambiguous ISO 8601 string. Returns None on failure.

    Times with an offset (``Z``, ``+02:00``, aware datetimes) are converted
    to UTC and returned naive, so every result can be compared with every
    other. Naive values are assumed to already be UTC.

    Regional formats like ``DD-MM-YYYY`` are intentionally not supported -
    callers needing them must use ``DateFormatRule`` with an explicit format.
    """
    parsed = None
    if isinstance(date_value, datetime):
        parsed = date_value
    elif isinstance(date_value, date):
        parsed = datetime(date_value.year, date_value.month, date_value.day)
    elif isinstance(date_value, str):
        for fmt in _ISO_DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_value, fmt)
                break
            except ValueError:
                continue

    if parsed is not None and parsed.utcoffset() is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _date_arg(rule: NitroValidationRule) -> datetime:
    """Return the first argument of ``rule`` as a datetime, or raise."""
    parsed = _parse_iso_date(rule.args[0])
    if parsed is None:
        raise NitroInvalidRuleError(
            f"Rule '{rule.name}' expects an ISO 8601 date, got {rule.args[0]!r}."
        )
    return parsed


# ============================================================================
# Basic Rules
# ============================================================================


class RequiredRule(NitroValidationRule):
    """Validate that a field is present and not empty."""

    name = "required"
    message = "The {field} field is required."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, (list, dict, tuple)) and len(value) == 0:
            return False
        return True


class OptionalRule(NitroValidationRule):
    """Mark a field as optional (always passes)."""

    name = "optional"
    message = ""

    def validate(self, field: str, value: Any, data: dict) -> bool:
        return True


# ============================================================================
# String Rules
# ============================================================================


class AlphaRule(NitroValidationRule):
    """Validate that a field contains only alphabetic characters."""

    name = "alpha"
    message = "The {field} field must contain only alphabetic characters."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        return isinstance(value, str) and value.isalpha()


class AlphanumericRule(NitroValidationRule):
    """Validate that a field contains only alphanumeric characters."""

    name = "alphanumeric"
    message = "The {field} field must contain only alphanumeric characters."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        return isinstance(value, str) and value.isalnum()


class EmailRule(NitroValidationRule):
    """Validate that a field is a valid email address."""

    name = "email"
    message = "The {field} field must be a valid email address."

    # Simple email regex pattern
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.EMAIL_PATTERN.fullmatch(value))


class UrlRule(NitroValidationRule):
    """Validate that a field is a valid http or https URL.

    The host may be a domain name (any TLD up to 63 characters, including
    punycode ``xn--`` TLDs), ``localhost``, an IPv4 address, or a bracketed
    IPv6 address. Ports must be in 1-65535.
    """

    name = "url"
    message = "The {field} field must be a valid URL."

    URL_PATTERN = re.compile(
        r"https?://"
        r"(?:"
        r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,63}|XN--[A-Z0-9-]{1,59})\.?"
        r"|localhost"
        r"|(?P<ipv4>[0-9]{1,3}(?:\.[0-9]{1,3}){3})"
        r"|\[(?P<ipv6>[0-9A-F:.]+)\]"
        r")"
        r"(?::(?P<port>[0-9]{1,5}))?"
        r"(?:[/?#]\S*)?",
        re.IGNORECASE,
    )

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        match = self.URL_PATTERN.fullmatch(value)
        if not match:
            return False
        if match.group("ipv4") and not _is_ip(match.group("ipv4"), ipaddress.IPv4Address):
            return False
        if match.group("ipv6") and not _is_ip(match.group("ipv6"), ipaddress.IPv6Address):
            return False
        port = match.group("port")
        return port is None or 1 <= int(port) <= 65535


class RegexRule(NitroValidationRule):
    """Validate that a field matches a regular expression.

    The pattern is applied with :func:`re.match`, so anchor it with ``$``
    or ``\\Z`` if the whole value must match. An invalid pattern raises
    :class:`NitroInvalidRuleError` when the rule is built.

    The pipe-delimited rule syntax splits on ``|`` and ``,``, so patterns
    containing those characters cannot be passed as a rule string. Build
    the rule directly instead, e.g. ``RegexRule(r"^(a|b)$")``.
    """

    name = "regex"
    message = "The {field} field format is invalid."
    min_args = 1

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        try:
            self._compiled = re.compile(self.args[0])
        except (re.error, TypeError) as error:
            raise NitroInvalidRuleError(
                f"Rule 'regex' got an invalid pattern {self.args[0]!r}: {error}"
            ) from error

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self._compiled.match(value))


class LowercaseRule(NitroValidationRule):
    """Validate that a field contains only lowercase characters."""

    name = "lowercase"
    message = "The {field} field must contain only lowercase characters."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return value.islower()


class UppercaseRule(NitroValidationRule):
    """Validate that a field contains only uppercase characters."""

    name = "uppercase"
    message = "The {field} field must contain only uppercase characters."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return value.isupper()


class AlphaDashRule(NitroValidationRule):
    """Validate that a field contains only letters, numbers, dashes, and underscores."""

    name = "alpha_dash"
    message = "The {field} field must contain only letters, numbers, dashes, and underscores."

    PATTERN = re.compile(r"[a-zA-Z0-9_-]+")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.fullmatch(value))


class StartsWithRule(NitroValidationRule):
    """Validate that a field starts with a given substring."""

    name = "starts_with"
    message = "The {field} field must start with {0}."
    min_args = 1

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        prefix = self.args[0]
        return value.startswith(prefix)


class EndsWithRule(NitroValidationRule):
    """Validate that a field ends with a given substring."""

    name = "ends_with"
    message = "The {field} field must end with {0}."
    min_args = 1

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        suffix = self.args[0]
        return value.endswith(suffix)


class ContainsRule(NitroValidationRule):
    """Validate that a field contains a given substring."""

    name = "contains"
    message = "The {field} field must contain {0}."
    min_args = 1

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        substring = self.args[0]
        return substring in value


class UuidRule(NitroValidationRule):
    """Validate that a field is a UUID in canonical 8-4-4-4-12 hex form."""

    name = "uuid"
    message = "The {field} field must be a valid UUID."

    PATTERN = re.compile(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    )

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.fullmatch(value))


def _is_ip(value: str, address_type: type) -> bool:
    """Return True if ``value`` parses as ``address_type``."""
    try:
        address_type(value)
        return True
    except ValueError:
        return False


class IpRule(NitroValidationRule):
    """Validate that a field is a valid IP address (v4 or v6)."""

    name = "ip"
    message = "The {field} field must be a valid IP address."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return _is_ip(value, ipaddress.IPv4Address) or _is_ip(value, ipaddress.IPv6Address)


class Ipv4Rule(NitroValidationRule):
    """Validate that a field is a valid IPv4 address."""

    name = "ipv4"
    message = "The {field} field must be a valid IPv4 address."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return _is_ip(value, ipaddress.IPv4Address)


class Ipv6Rule(NitroValidationRule):
    """Validate that a field is a valid IPv6 address."""

    name = "ipv6"
    message = "The {field} field must be a valid IPv6 address."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return _is_ip(value, ipaddress.IPv6Address)


class JsonRule(NitroValidationRule):
    """Validate that a field is a valid JSON string."""

    name = "json"
    message = "The {field} field must be valid JSON."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        try:
            json_module.loads(value)
            return True
        except (ValueError, TypeError):
            return False


class SlugRule(NitroValidationRule):
    """Validate that a field is a valid URL slug."""

    name = "slug"
    message = "The {field} field must be a valid slug (lowercase letters, numbers, and hyphens)."

    PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.fullmatch(value))


# ============================================================================
# Numeric Rules
# ============================================================================


class NumericRule(NitroValidationRule):
    """Validate that a field is a finite number, or a string holding one."""

    name = "numeric"
    message = "The {field} field must be numeric."
    implies_numeric = True

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        return _to_number(value) is not None


class IntegerRule(NitroValidationRule):
    """Validate that a field is an integer, or a string of digits."""

    name = "integer"
    message = "The {field} field must be an integer."
    implies_numeric = True

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        return isinstance(_to_number(value), int)


class _MeasuredRule(NitroValidationRule):
    """Base for rules that compare a number, a length, or a collection size.

    Numbers are compared by value. Strings, lists, dicts and tuples are
    compared by length, unless the field also has ``numeric`` or
    ``integer``, in which case numeric strings are compared by value.
    """

    numeric = False

    def as_numeric(self) -> "NitroValidationRule":
        rule = copy.copy(self)
        rule.numeric = True
        return rule

    def _measure(self, value: Any) -> Optional[Number]:
        if isinstance(value, (bool, int, float)) or self.numeric:
            return _to_number(value)
        if isinstance(value, (str, list, dict, tuple)):
            return len(value)
        return None


class MinRule(_MeasuredRule):
    """Validate that a field has a minimum value or length."""

    name = "min"
    message = "The {field} field must be at least {0}."
    min_args = 1

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.limit = _number_arg(self, 0)

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        measured = self._measure(value)
        return measured is not None and measured >= self.limit


class MaxRule(_MeasuredRule):
    """Validate that a field has a maximum value or length."""

    name = "max"
    message = "The {field} field must not exceed {0}."
    min_args = 1

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.limit = _number_arg(self, 0)

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        measured = self._measure(value)
        return measured is not None and measured <= self.limit


class BetweenRule(_MeasuredRule):
    """Validate that a field is between two values (inclusive)."""

    name = "between"
    message = "The {field} field must be between {0} and {1}."
    min_args = 2

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.lower = _number_arg(self, 0)
        self.upper = _number_arg(self, 1)

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        measured = self._measure(value)
        return measured is not None and self.lower <= measured <= self.upper


class PositiveRule(NitroValidationRule):
    """Validate that a field is a positive number."""

    name = "positive"
    message = "The {field} field must be a positive number."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        number = _to_number(value)
        return number is not None and number > 0


class NegativeRule(NitroValidationRule):
    """Validate that a field is a negative number."""

    name = "negative"
    message = "The {field} field must be a negative number."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        number = _to_number(value)
        return number is not None and number < 0


class DivisibleByRule(NitroValidationRule):
    """Validate that a field is divisible by a given number.

    Integers are checked with exact integer arithmetic, so very large
    values don't lose precision. Anything involving a float is checked in
    decimal, so ``0.3`` counts as divisible by ``0.1``.
    """

    name = "divisible_by"
    message = "The {field} field must be divisible by {0}."
    min_args = 1

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.divisor = _number_arg(self, 0)
        if self.divisor == 0:
            raise NitroInvalidRuleError("Rule 'divisible_by' can't divide by zero.")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        number = _to_number(value)
        if number is None:
            return False
        if isinstance(number, int) and isinstance(self.divisor, int):
            return number % self.divisor == 0
        try:
            return Decimal(repr(number)) % Decimal(repr(self.divisor)) == 0
        except InvalidOperation:
            return False


# ============================================================================
# Comparison Rules
# ============================================================================


class SameRule(NitroValidationRule):
    """Validate that a field matches another field."""

    name = "same"
    message = "The {field} field must match {0}."
    min_args = 1

    def validate(self, field: str, value: Any, data: dict) -> bool:
        other_field = self.args[0]
        other_value = data.get(other_field)

        return value == other_value


class DifferentRule(NitroValidationRule):
    """Validate that a field is different from another field."""

    name = "different"
    message = "The {field} field must be different from {0}."
    min_args = 1

    def validate(self, field: str, value: Any, data: dict) -> bool:
        other_field = self.args[0]
        other_value = data.get(other_field)

        return value != other_value


def _value_matches_arg(value: Any, args: tuple) -> bool:
    """Return True if ``value`` matches any entry in ``args``.

    Compares directly first, then falls back to string-vs-numeric
    matching so that ``1`` matches ``("1", "2", "3")`` (the form rule
    arguments take when parsed from a rule string).
    """
    if value in args:
        return True
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        if str(value) in args:
            return True
        for arg in args:
            if isinstance(arg, str):
                try:
                    if float(arg) == float(value):
                        return True
                except ValueError:
                    continue
    return False


class InRule(NitroValidationRule):
    """Validate that a field is in a list of values.

    When the rule is parsed from a string (``"in:1,2,3"``) every argument
    arrives as a string. Numeric values are still matched correctly: an
    integer ``1`` compares equal to the string ``"1"``.
    """

    name = "in"
    message = "The {field} field must be one of: {args}."
    min_args = 1

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        return _value_matches_arg(value, self.args)


class NotInRule(NitroValidationRule):
    """Validate that a field is not in a list of values."""

    name = "not_in"
    message = "The {field} field must not be one of: {args}."
    min_args = 1

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        return not _value_matches_arg(value, self.args)


# ============================================================================
# Boolean Rules
# ============================================================================


class BooleanRule(NitroValidationRule):
    """Validate that a field is a boolean value."""

    name = "boolean"
    message = "The {field} field must be true or false."

    TRUTHY_VALUES = [True, "true", "True", "1", 1, "yes", "Yes", "on", "On"]
    FALSY_VALUES = [False, "false", "False", "0", 0, "no", "No", "off", "Off"]

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        return value in self.TRUTHY_VALUES or value in self.FALSY_VALUES


# ============================================================================
# Date/Time Rules
# ============================================================================


class DateRule(NitroValidationRule):
    """Validate that a field is a valid date.

    Accepts ``date`` and ``datetime`` objects, and unambiguous ISO 8601
    strings: ``YYYY-MM-DD``, ``YYYY/MM/DD``, ``YYYY-MM-DDTHH:MM:SS`` with
    optional fractional seconds and an optional ``Z`` or ``+HH:MM`` offset.
    Regional formats must go through :class:`DateFormatRule` with an
    explicit ``strptime`` string to avoid locale ambiguity.
    """

    name = "date"
    message = "The {field} field must be a valid date."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        return _parse_iso_date(value) is not None


class BeforeRule(NitroValidationRule):
    """Validate that a date field is before a given date."""

    name = "before"
    message = "The {field} field must be a date before {0}."
    min_args = 1

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.compare = _date_arg(self)

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        value_date = _parse_iso_date(value)
        return value_date is not None and value_date < self.compare


class AfterRule(NitroValidationRule):
    """Validate that a date field is after a given date."""

    name = "after"
    message = "The {field} field must be a date after {0}."
    min_args = 1

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.compare = _date_arg(self)

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        value_date = _parse_iso_date(value)
        return value_date is not None and value_date > self.compare


class DateEqualsRule(NitroValidationRule):
    """Validate that a date field equals a given date."""

    name = "date_equals"
    message = "The {field} field must be a date equal to {0}."
    min_args = 1

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.compare = _date_arg(self)

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        value_date = _parse_iso_date(value)
        return value_date is not None and value_date.date() == self.compare.date()


class DateFormatRule(NitroValidationRule):
    """Validate that a date field matches a specific format."""

    name = "date_format"
    message = "The {field} field must be a date in format {0}."
    min_args = 1

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        date_format = self.args[0]
        try:
            datetime.strptime(value, date_format)
            return True
        except (ValueError, re.error):
            return False


# ============================================================================
# Convenience Rules
# ============================================================================


class ConfirmedRule(NitroValidationRule):
    """Validate that a field matches its confirmation field (field_confirmation).

    Skips the check when the field itself is empty: presence is the job
    of ``required``. Pair with ``required`` if a missing field should
    fail confirmation.
    """

    name = "confirmed"
    message = "The {field} confirmation does not match."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        confirmation_field = f"{field}_confirmation"
        confirmation_value = data.get(confirmation_field)

        return value == confirmation_value


class AcceptedRule(NitroValidationRule):
    """Validate that a field has been accepted (yes, true, 1, on)."""

    name = "accepted"
    message = "The {field} must be accepted."

    ACCEPTED_VALUES = [True, "true", "True", "1", 1, "yes", "Yes", "on", "On"]

    def validate(self, field: str, value: Any, data: dict) -> bool:
        return value in self.ACCEPTED_VALUES


class DeclinedRule(NitroValidationRule):
    """Validate that a field has been declined (no, false, 0, off)."""

    name = "declined"
    message = "The {field} must be declined."

    DECLINED_VALUES = [False, "false", "False", "0", 0, "no", "No", "off", "Off"]

    def validate(self, field: str, value: Any, data: dict) -> bool:
        return value in self.DECLINED_VALUES


# ============================================================================
# Length Rules
# ============================================================================


class LengthRule(NitroValidationRule):
    """Validate that a field has an exact length."""

    name = "length"
    message = "The {field} field must be exactly {0} characters."
    min_args = 1

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.target = _number_arg(self, 0)
        if not isinstance(self.target, int):
            raise NitroInvalidRuleError(
                f"Rule 'length' expects a whole number, got {self.args[0]!r}."
            )

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, (str, list, dict, tuple)):
            return len(value) == self.target
        return False


# ============================================================================
# String Content Rules
# ============================================================================


class AsciiRule(NitroValidationRule):
    """Validate that a field contains only ASCII characters."""

    name = "ascii"
    message = "The {field} field must contain only ASCII characters."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        try:
            value.encode("ascii")
            return True
        except UnicodeEncodeError:
            return False


class Base64Rule(NitroValidationRule):
    """Validate that a field is valid base64 encoding."""

    name = "base64"
    message = "The {field} field must be valid base64 encoding."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        import base64

        try:
            # Try to decode the base64 string
            decoded = base64.b64decode(value, validate=True)
            # Try to encode it back and compare
            encoded = base64.b64encode(decoded).decode("ascii")
            # Remove potential padding differences
            return value.rstrip("=") == encoded.rstrip("=")
        except Exception:
            return False


class HexColorRule(NitroValidationRule):
    """Validate that a field is a valid hex color code."""

    name = "hex_color"
    message = "The {field} field must be a valid hex color (e.g., #fff or #ffffff)."

    PATTERN = re.compile(r"#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.fullmatch(value))


class CreditCardRule(NitroValidationRule):
    """Validate that a field is a valid credit card number using Luhn algorithm."""

    name = "credit_card"
    message = "The {field} field must be a valid credit card number."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        # Remove spaces and dashes
        card_number = value.replace(" ", "").replace("-", "")

        # Check if it contains only digits
        if not card_number.isdigit():
            return False

        # Credit cards are typically 13-19 digits
        if len(card_number) < 13 or len(card_number) > 19:
            return False

        # Luhn algorithm
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]

            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10

        return luhn_checksum(card_number) == 0


class MacAddressRule(NitroValidationRule):
    """Validate that a field is a valid MAC address."""

    name = "mac_address"
    message = "The {field} field must be a valid MAC address."

    # Supports formats: AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF, AABBCCDDEEFF
    PATTERNS = [
        re.compile(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"),  # With : or -
        re.compile(r"[0-9A-Fa-f]{12}"),  # Without separator
    ]

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        return any(pattern.fullmatch(value) for pattern in self.PATTERNS)


# ============================================================================
# Collection Rules
# ============================================================================


class ArrayRule(NitroValidationRule):
    """Validate that a field is an array/list."""

    name = "array"
    message = "The {field} field must be an array."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        return isinstance(value, (list, tuple))


class SizeRule(_MeasuredRule):
    """Validate that a field has an exact size (value, length, or item count)."""

    name = "size"
    message = "The {field} field must be exactly {0}."
    min_args = 1

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.target = _number_arg(self, 0)

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        measured = self._measure(value)
        return measured is not None and measured == self.target


class DistinctRule(NitroValidationRule):
    """Validate that an array contains only unique values."""

    name = "distinct"
    message = "The {field} field must contain only unique values."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        if not isinstance(value, (list, tuple)):
            return False

        # Check if all values are unique
        try:
            return len(value) == len(set(value))
        except TypeError:
            # If values are not hashable (like dicts), compare manually
            seen = []
            for item in value:
                if item in seen:
                    return False
                seen.append(item)
            return True


# ============================================================================
# Advanced String Rules
# ============================================================================


@functools.lru_cache(maxsize=None)
def _iana_zones() -> Optional[FrozenSet[str]]:
    """Return every IANA zone name, or None when no tz database is available."""
    try:
        import zoneinfo
    except ImportError:
        return None
    return frozenset(zoneinfo.available_timezones()) or None


class TimezoneRule(NitroValidationRule):
    """Validate that a field is a valid IANA timezone identifier.

    When the IANA database is available (Python 3.9+ with system tz data
    or the ``tzdata`` package) the value must be a real zone name. When it
    isn't (Python 3.7/3.8, or Windows without ``tzdata``) the rule falls
    back to a structural check that accepts ``UTC``, ``GMT``, and
    ``Area/Location`` shapes such as ``America/New_York`` or ``Etc/GMT+5``.
    Fixed offsets like ``+02:00`` are rejected either way.
    """

    name = "timezone"
    message = "The {field} field must be a valid timezone."

    _FALLBACK_PATTERN = re.compile(r"UTC|GMT|[A-Za-z][A-Za-z0-9_+\-]*(/[A-Za-z0-9_+\-]+)+")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        zones = _iana_zones()
        if zones is None:
            return bool(self._FALLBACK_PATTERN.fullmatch(value))
        return value in zones


class LocaleRule(NitroValidationRule):
    """Validate that a field is a valid locale code."""

    name = "locale"
    message = "The {field} field must be a valid locale code."

    # Common locale pattern: en_US, en-US, en, pt_BR, etc.
    PATTERN = re.compile(r"[a-z]{2,3}([_-][A-Z]{2})?")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.fullmatch(value))
