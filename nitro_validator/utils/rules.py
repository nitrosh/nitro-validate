"""
Built-in validation rules for nitro-validator.
"""

import re
import uuid as uuid_module
import json as json_module
from datetime import datetime
from typing import Any, Optional, Tuple
from ..core.rule import NitroValidationRule


_ISO_DATE_FORMATS: Tuple[str, ...] = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
)


def _parse_iso_date(date_value: Any) -> Optional[datetime]:
    """Parse a datetime or unambiguous ISO 8601 string. Returns None on failure.

    Regional formats like ``DD-MM-YYYY`` are intentionally not supported -
    callers needing them must use ``DateFormatRule`` with an explicit format.
    """
    if isinstance(date_value, datetime):
        return date_value
    if not isinstance(date_value, str):
        return None
    for fmt in _ISO_DATE_FORMATS:
        try:
            return datetime.strptime(date_value, fmt)
        except ValueError:
            continue
    return None


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
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.EMAIL_PATTERN.match(value))


class UrlRule(NitroValidationRule):
    """Validate that a field is a valid URL."""

    name = "url"
    message = "The {field} field must be a valid URL."

    URL_PATTERN = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.URL_PATTERN.match(value))


class RegexRule(NitroValidationRule):
    """Validate that a field matches a regular expression.

    The pipe-delimited rule syntax splits on ``|`` and ``,``, so patterns
    containing those characters cannot be passed as a rule string. Build
    the rule directly instead, e.g. ``RegexRule(r"^(a|b)$")``.
    """

    name = "regex"
    message = "The {field} field format is invalid."

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._compiled = None
        if self.args:
            try:
                self._compiled = re.compile(self.args[0])
            except re.error:
                self._compiled = None

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        if self._compiled is None:
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

    PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.match(value))


class StartsWithRule(NitroValidationRule):
    """Validate that a field starts with a given substring."""

    name = "starts_with"
    message = "The {field} field must start with {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        if not self.args:
            return False

        prefix = self.args[0]
        return value.startswith(prefix)


class EndsWithRule(NitroValidationRule):
    """Validate that a field ends with a given substring."""

    name = "ends_with"
    message = "The {field} field must end with {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        if not self.args:
            return False

        suffix = self.args[0]
        return value.endswith(suffix)


class ContainsRule(NitroValidationRule):
    """Validate that a field contains a given substring."""

    name = "contains"
    message = "The {field} field must contain {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        if not self.args:
            return False

        substring = self.args[0]
        return substring in value


class UuidRule(NitroValidationRule):
    """Validate that a field is a valid UUID."""

    name = "uuid"
    message = "The {field} field must be a valid UUID."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        try:
            uuid_module.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False


class IpRule(NitroValidationRule):
    """Validate that a field is a valid IP address (v4 or v6)."""

    name = "ip"
    message = "The {field} field must be a valid IP address."

    IPV4_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    IPV6_PATTERN = re.compile(
        r"^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,7}:|"
        r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|"
        r"([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
        r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|"
        r"[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|"
        r":((:[0-9a-fA-F]{1,4}){1,7}|:))$"
    )

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        if self.IPV4_PATTERN.match(value):
            return True
        return bool(self.IPV6_PATTERN.match(value))


class Ipv4Rule(NitroValidationRule):
    """Validate that a field is a valid IPv4 address."""

    name = "ipv4"
    message = "The {field} field must be a valid IPv4 address."

    PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.match(value))


class Ipv6Rule(NitroValidationRule):
    """Validate that a field is a valid IPv6 address."""

    name = "ipv6"
    message = "The {field} field must be a valid IPv6 address."

    PATTERN = re.compile(
        r"^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,7}:|"
        r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|"
        r"([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
        r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|"
        r"[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|"
        r":((:[0-9a-fA-F]{1,4}){1,7}|:))$"
    )

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.match(value))


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

    PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.match(value))


# ============================================================================
# Numeric Rules
# ============================================================================


class NumericRule(NitroValidationRule):
    """Validate that a field is numeric."""

    name = "numeric"
    message = "The {field} field must be numeric."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        if isinstance(value, bool):
            return False

        if isinstance(value, (int, float)):
            return True

        if isinstance(value, str):
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False

        return False


class IntegerRule(NitroValidationRule):
    """Validate that a field is an integer."""

    name = "integer"
    message = "The {field} field must be an integer."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        if isinstance(value, bool):  # bool is instance of int, so exclude it
            return False

        if isinstance(value, int):
            return True

        if isinstance(value, str):
            try:
                int(value)
                return True
            except (ValueError, TypeError):
                return False

        return False


class MinRule(NitroValidationRule):
    """Validate that a field has a minimum value or length."""

    name = "min"
    message = "The {field} field must be at least {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        min_value = self.args[0] if self.args else 0

        if isinstance(min_value, str):
            if "." in min_value:
                min_value = float(min_value)
            else:
                min_value = int(min_value)

        if isinstance(value, bool):
            return False

        if isinstance(value, (int, float)):
            return value >= min_value

        if isinstance(value, str):
            return len(value) >= min_value

        if isinstance(value, (list, dict, tuple)):
            return len(value) >= min_value

        return False


class MaxRule(NitroValidationRule):
    """Validate that a field has a maximum value or length."""

    name = "max"
    message = "The {field} field must not exceed {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        max_value = self.args[0] if self.args else 0

        if isinstance(max_value, str):
            if "." in max_value:
                max_value = float(max_value)
            else:
                max_value = int(max_value)

        if isinstance(value, bool):
            return False

        if isinstance(value, (int, float)):
            return value <= max_value

        if isinstance(value, str):
            return len(value) <= max_value

        if isinstance(value, (list, dict, tuple)):
            return len(value) <= max_value

        return False


class BetweenRule(NitroValidationRule):
    """Validate that a field is between two values."""

    name = "between"
    message = "The {field} field must be between {0} and {1}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        if len(self.args) < 2:
            return False

        min_value = self.args[0]
        max_value = self.args[1]

        if isinstance(min_value, str):
            if "." in min_value:
                min_value = float(min_value)
            else:
                min_value = int(min_value)

        if isinstance(max_value, str):
            if "." in max_value:
                max_value = float(max_value)
            else:
                max_value = int(max_value)

        if isinstance(value, bool):
            return False

        if isinstance(value, (int, float)):
            return min_value <= value <= max_value

        if isinstance(value, str):
            return min_value <= len(value) <= max_value

        if isinstance(value, (list, dict, tuple)):
            return min_value <= len(value) <= max_value

        return False


class PositiveRule(NitroValidationRule):
    """Validate that a field is a positive number."""

    name = "positive"
    message = "The {field} field must be a positive number."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        if isinstance(value, bool):
            return False

        try:
            num_value = float(value) if isinstance(value, str) else value
            return isinstance(num_value, (int, float)) and num_value > 0
        except (ValueError, TypeError):
            return False


class NegativeRule(NitroValidationRule):
    """Validate that a field is a negative number."""

    name = "negative"
    message = "The {field} field must be a negative number."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        if isinstance(value, bool):
            return False

        try:
            num_value = float(value) if isinstance(value, str) else value
            return isinstance(num_value, (int, float)) and num_value < 0
        except (ValueError, TypeError):
            return False


class DivisibleByRule(NitroValidationRule):
    """Validate that a field is divisible by a given number.

    For float operands the remainder is compared against a small epsilon
    to avoid spurious failures from binary floating-point representation
    (e.g. ``1.0 % 0.1`` is not exactly zero).
    """

    name = "divisible_by"
    message = "The {field} field must be divisible by {0}."

    _FLOAT_EPSILON = 1e-9

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        if not self.args:
            return False

        if isinstance(value, bool):
            return False

        try:
            divisor = float(self.args[0]) if isinstance(self.args[0], str) else self.args[0]
            num_value = float(value) if isinstance(value, str) else value

            if not isinstance(num_value, (int, float)) or divisor == 0:
                return False

            if isinstance(num_value, float) or isinstance(divisor, float):
                remainder = abs(num_value % divisor)
                return (
                    remainder < self._FLOAT_EPSILON
                    or abs(remainder - abs(divisor)) < self._FLOAT_EPSILON
                )

            return num_value % divisor == 0
        except (ValueError, TypeError):
            return False


# ============================================================================
# Comparison Rules
# ============================================================================


class SameRule(NitroValidationRule):
    """Validate that a field matches another field."""

    name = "same"
    message = "The {field} field must match {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if not self.args:
            return False

        other_field = self.args[0]
        other_value = data.get(other_field)

        return value == other_value


class DifferentRule(NitroValidationRule):
    """Validate that a field is different from another field."""

    name = "different"
    message = "The {field} field must be different from {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if not self.args:
            return False

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

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        return _value_matches_arg(value, self.args)


class NotInRule(NitroValidationRule):
    """Validate that a field is not in a list of values."""

    name = "not_in"
    message = "The {field} field must not be one of: {args}."

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

    Only unambiguous ISO 8601 strings (``YYYY-MM-DD``, ``YYYY/MM/DD``,
    ``YYYY-MM-DDTHH:MM:SS``) are accepted. Regional formats must go
    through :class:`DateFormatRule` with an explicit ``strptime`` string
    to avoid locale ambiguity.
    """

    name = "date"
    message = "The {field} field must be a valid date."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, (str, datetime)):
            return False
        return _parse_iso_date(value) is not None


class BeforeRule(NitroValidationRule):
    """Validate that a date field is before a given date."""

    name = "before"
    message = "The {field} field must be a date before {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not self.args:
            return False
        value_date = _parse_iso_date(value)
        compare_date = _parse_iso_date(self.args[0])
        if value_date is None or compare_date is None:
            return False
        return value_date < compare_date


class AfterRule(NitroValidationRule):
    """Validate that a date field is after a given date."""

    name = "after"
    message = "The {field} field must be a date after {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not self.args:
            return False
        value_date = _parse_iso_date(value)
        compare_date = _parse_iso_date(self.args[0])
        if value_date is None or compare_date is None:
            return False
        return value_date > compare_date


class DateEqualsRule(NitroValidationRule):
    """Validate that a date field equals a given date."""

    name = "date_equals"
    message = "The {field} field must be a date equal to {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not self.args:
            return False
        value_date = _parse_iso_date(value)
        compare_date = _parse_iso_date(self.args[0])
        if value_date is None or compare_date is None:
            return False
        return value_date.date() == compare_date.date()


class DateFormatRule(NitroValidationRule):
    """Validate that a date field matches a specific format."""

    name = "date_format"
    message = "The {field} field must be a date in format {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not self.args:
            return False
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

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        if not self.args:
            return False

        target_length = int(self.args[0])

        if isinstance(value, str):
            return len(value) == target_length

        if isinstance(value, (list, dict, tuple)):
            return len(value) == target_length

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

    PATTERN = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.match(value))


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
        re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"),  # With : or -
        re.compile(r"^[0-9A-Fa-f]{12}$"),  # Without separator
    ]

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        return any(pattern.match(value) for pattern in self.PATTERNS)


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


class SizeRule(NitroValidationRule):
    """Validate that a field has an exact size (length/size/value)."""

    name = "size"
    message = "The {field} field must be exactly {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True

        if not self.args:
            return False

        target_size = self.args[0]

        if isinstance(target_size, str):
            if "." in target_size:
                target_size = float(target_size)
            else:
                target_size = int(target_size)

        if isinstance(value, bool):
            return False

        if isinstance(value, (int, float)):
            return value == target_size

        if isinstance(value, (str, list, dict, tuple)):
            return len(value) == target_size

        return False


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


class TimezoneRule(NitroValidationRule):
    """Validate that a field is a valid timezone identifier.

    On Python 3.9+ the canonical IANA database is consulted via
    :mod:`zoneinfo`. On older interpreters (3.7, 3.8) the rule falls
    back to a permissive structural regex that accepts ``UTC``, ``GMT``,
    fixed offsets like ``+02:00``, and ``Area/Location`` zones including
    ones with digits, mixed case, or extra path segments
    (e.g. ``America/New_York``, ``Etc/GMT+5``, ``US/Eastern``).
    """

    name = "timezone"
    message = "The {field} field must be a valid timezone."

    _FALLBACK_PATTERN = re.compile(
        r"^(" r"UTC|GMT" r"|[+-]\d{2}:?\d{2}" r"|[A-Za-z][A-Za-z0-9_+\-]*(/[A-Za-z0-9_+\-]+)+" r")$"
    )

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        try:
            import zoneinfo

            zoneinfo.ZoneInfo(value)
            return True
        except ImportError:
            return bool(self._FALLBACK_PATTERN.match(value))
        except Exception:
            return False


class LocaleRule(NitroValidationRule):
    """Validate that a field is a valid locale code."""

    name = "locale"
    message = "The {field} field must be a valid locale code."

    # Common locale pattern: en_US, en-US, en, pt_BR, etc.
    PATTERN = re.compile(r"^[a-z]{2,3}([_-][A-Z]{2})?$")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        # Check pattern
        if not self.PATTERN.match(value):
            return False

        # Pattern matched, locale is valid
        return True
