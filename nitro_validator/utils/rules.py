"""
Built-in validation rules for nitro-validator.
"""

import re
from typing import Any
from ..core.rule import Rule


# ============================================================================
# Basic Rules
# ============================================================================

class RequiredRule(Rule):
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


class OptionalRule(Rule):
    """Mark a field as optional (always passes)."""

    name = "optional"
    message = ""

    def validate(self, field: str, value: Any, data: dict) -> bool:
        return True


# ============================================================================
# String Rules
# ============================================================================

class AlphaRule(Rule):
    """Validate that a field contains only alphabetic characters."""

    name = "alpha"
    message = "The {field} field must contain only alphabetic characters."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True
        return isinstance(value, str) and value.isalpha()


class AlphanumericRule(Rule):
    """Validate that a field contains only alphanumeric characters."""

    name = "alphanumeric"
    message = "The {field} field must contain only alphanumeric characters."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True
        return isinstance(value, str) and value.isalnum()


class EmailRule(Rule):
    """Validate that a field is a valid email address."""

    name = "email"
    message = "The {field} field must be a valid email address."

    # Simple email regex pattern
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True
        if not isinstance(value, str):
            return False
        return bool(self.EMAIL_PATTERN.match(value))


class UrlRule(Rule):
    """Validate that a field is a valid URL."""

    name = "url"
    message = "The {field} field must be a valid URL."

    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True
        if not isinstance(value, str):
            return False
        return bool(self.URL_PATTERN.match(value))


class RegexRule(Rule):
    """Validate that a field matches a regular expression."""

    name = "regex"
    message = "The {field} field format is invalid."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True
        if not isinstance(value, str):
            return False

        pattern = self.args[0] if self.args else None
        if not pattern:
            return False

        return bool(re.match(pattern, value))


# ============================================================================
# Numeric Rules
# ============================================================================

class NumericRule(Rule):
    """Validate that a field is numeric."""

    name = "numeric"
    message = "The {field} field must be numeric."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True

        if isinstance(value, (int, float)):
            return True

        if isinstance(value, str):
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False

        return False


class IntegerRule(Rule):
    """Validate that a field is an integer."""

    name = "integer"
    message = "The {field} field must be an integer."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
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


class MinRule(Rule):
    """Validate that a field has a minimum value or length."""

    name = "min"
    message = "The {field} field must be at least {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True

        min_value = self.args[0] if self.args else 0

        # Convert string to appropriate type
        if isinstance(min_value, str):
            if '.' in min_value:
                min_value = float(min_value)
            else:
                min_value = int(min_value)

        # Check numeric values
        if isinstance(value, (int, float)):
            return value >= min_value

        # Check string length
        if isinstance(value, str):
            return len(value) >= min_value

        # Check collection size
        if isinstance(value, (list, dict, tuple)):
            return len(value) >= min_value

        return False


class MaxRule(Rule):
    """Validate that a field has a maximum value or length."""

    name = "max"
    message = "The {field} field must not exceed {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True

        max_value = self.args[0] if self.args else 0

        # Convert string to appropriate type
        if isinstance(max_value, str):
            if '.' in max_value:
                max_value = float(max_value)
            else:
                max_value = int(max_value)

        # Check numeric values
        if isinstance(value, (int, float)):
            return value <= max_value

        # Check string length
        if isinstance(value, str):
            return len(value) <= max_value

        # Check collection size
        if isinstance(value, (list, dict, tuple)):
            return len(value) <= max_value

        return False


class BetweenRule(Rule):
    """Validate that a field is between two values."""

    name = "between"
    message = "The {field} field must be between {0} and {1}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True

        if len(self.args) < 2:
            return False

        min_value = self.args[0]
        max_value = self.args[1]

        # Convert strings to appropriate types
        if isinstance(min_value, str):
            if '.' in min_value:
                min_value = float(min_value)
            else:
                min_value = int(min_value)

        if isinstance(max_value, str):
            if '.' in max_value:
                max_value = float(max_value)
            else:
                max_value = int(max_value)

        # Check numeric values
        if isinstance(value, (int, float)):
            return min_value <= value <= max_value

        # Check string length
        if isinstance(value, str):
            return min_value <= len(value) <= max_value

        # Check collection size
        if isinstance(value, (list, dict, tuple)):
            return min_value <= len(value) <= max_value

        return False


# ============================================================================
# Comparison Rules
# ============================================================================

class SameRule(Rule):
    """Validate that a field matches another field."""

    name = "same"
    message = "The {field} field must match {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if not self.args:
            return False

        other_field = self.args[0]
        other_value = data.get(other_field)

        return value == other_value


class DifferentRule(Rule):
    """Validate that a field is different from another field."""

    name = "different"
    message = "The {field} field must be different from {0}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if not self.args:
            return False

        other_field = self.args[0]
        other_value = data.get(other_field)

        return value != other_value


class InRule(Rule):
    """Validate that a field is in a list of values."""

    name = "in"
    message = "The {field} field must be one of: {args}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True

        return value in self.args


class NotInRule(Rule):
    """Validate that a field is not in a list of values."""

    name = "not_in"
    message = "The {field} field must not be one of: {args}."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True

        return value not in self.args


# ============================================================================
# Boolean Rules
# ============================================================================

class BooleanRule(Rule):
    """Validate that a field is a boolean value."""

    name = "boolean"
    message = "The {field} field must be true or false."

    TRUTHY_VALUES = [True, 'true', 'True', '1', 1, 'yes', 'Yes', 'on', 'On']
    FALSY_VALUES = [False, 'false', 'False', '0', 0, 'no', 'No', 'off', 'Off']

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True

        return value in self.TRUTHY_VALUES or value in self.FALSY_VALUES


# ============================================================================
# Date/Time Rules
# ============================================================================

class DateRule(Rule):
    """Validate that a field is a valid date."""

    name = "date"
    message = "The {field} field must be a valid date."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True

        from datetime import datetime

        if isinstance(value, datetime):
            return True

        if not isinstance(value, str):
            return False

        # Try to parse common date formats
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%m-%d-%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
        ]

        for fmt in date_formats:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue

        return False


# ============================================================================
# Length Rules
# ============================================================================

class LengthRule(Rule):
    """Validate that a field has an exact length."""

    name = "length"
    message = "The {field} field must be exactly {0} characters."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if value is None or value == '':
            return True

        if not self.args:
            return False

        target_length = int(self.args[0])

        if isinstance(value, str):
            return len(value) == target_length

        if isinstance(value, (list, dict, tuple)):
            return len(value) == target_length

        return False
