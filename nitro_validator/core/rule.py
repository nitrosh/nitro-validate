"""
Base NitroValidationRule class for validation rules.
"""

from typing import Any


class NitroValidationRule:
    """Base class for every validation rule in nitro-validator.

    Subclass this to add a new rule. Set two class attributes and
    implement :meth:`validate`:

    * ``name`` — the string used in pipe-delimited rule syntax
      (e.g. ``"required"``, ``"min"``).
    * ``message`` — the default error template. Placeholders ``{field}``,
      ``{args}``, and positional ``{0}``, ``{1}``, ... are substituted
      by :meth:`get_message`.

    A rule instance carries its positional arguments in ``self.args`` —
    these come from the colon/comma-delimited tail of a rule string
    (``"between:1,100"`` → ``args == ("1", "100")``), always as strings
    when parsed from a rule string, so cast inside :meth:`validate` if
    you need numbers.

    Convention: return ``True`` for ``None`` or empty string in every rule
    *except* presence checks (``required``, ``accepted``, ``declined``).
    This lets callers compose rules like ``"email"`` with an optional
    field by omitting ``required``.

    Attributes:
        name: Class-level identifier used by the rule registry.
        message: Class-level default error template.
        args: Positional arguments the rule was instantiated with.
        kwargs: Keyword arguments (reserved; ``message`` is extracted).
        custom_message: Per-instance override applied by the validator
            when the caller passes custom messages.

    Example:
        >>> from nitro_validator import NitroValidationRule, NitroValidator
        >>> class StartsUpperRule(NitroValidationRule):
        ...     name = "starts_upper"
        ...     message = "The {field} field must start with an uppercase letter."
        ...     def validate(self, field, value, data):
        ...         if not value:
        ...             return True  # let `required` enforce presence
        ...         return isinstance(value, str) and value[:1].isupper()
        >>> v = NitroValidator()
        >>> v.register_rule(StartsUpperRule)
        >>> v.is_valid({'name': 'Alice'}, {'name': 'starts_upper'})
        True
    """

    name = None  # Rule name (e.g., 'required', 'email', 'min')
    message = "The {field} field is invalid."  # Default error message

    def __init__(self, *args: Any, **kwargs: Any):
        """Store the rule's positional and keyword arguments.

        Rule strings like ``"between:1,100"`` are parsed into
        ``*args = ("1", "100")`` — arguments therefore arrive as
        strings and must be cast inside :meth:`validate`. Pass
        ``message=`` to override the default template for this
        instance only.

        Args:
            *args: Positional rule arguments (e.g. min value, pattern).
            **kwargs: Reserved keyword options. ``message`` becomes
                ``self.custom_message``.
        """
        self.args = args
        self.kwargs = kwargs
        self.custom_message = kwargs.get("message")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        """Return ``True`` if ``value`` passes this rule, otherwise ``False``.

        Subclasses must override this method. The full ``data`` dict is
        provided so cross-field rules (``same``, ``confirmed``, ...) can
        peek at sibling values.

        Args:
            field: Name of the field being validated.
            value: The value to check.
            data: The full data dict under validation.

        Returns:
            ``True`` to accept the value, ``False`` to mark the field as
            failing this rule.

        Raises:
            NotImplementedError: If a subclass does not override this.
        """
        raise NotImplementedError("Subclasses must implement validate()")

    def get_message(self, field: str) -> str:
        """Return the formatted error message for a failing field.

        Uses ``self.custom_message`` when set (e.g. via the validator's
        ``messages`` argument), otherwise the class-level ``message``.
        Substitutes ``{field}``, ``{args}`` (comma-joined), and
        positional placeholders ``{0}``, ``{1}``, ... from ``self.args``.

        Args:
            field: Name of the failing field to substitute into the
                message template.

        Returns:
            The rendered error message.

        Example:
            >>> rule = NitroValidationRule("18")
            >>> rule.message = "The {field} must be at least {0}."
            >>> rule.get_message("age")
            'The age must be at least 18.'
        """
        message = self.custom_message or self.message

        # Replace placeholders in message
        replacements = {
            "{field}": field,
            "{args}": ", ".join(str(arg) for arg in self.args) if self.args else "",
        }

        # Add indexed args for specific replacements like {0}, {1}, etc.
        for i, arg in enumerate(self.args):
            replacements[f"{{{i}}}"] = str(arg)

        for placeholder, value in replacements.items():
            message = message.replace(placeholder, value)

        return message

    def __repr__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.args) if self.args else ""
        return f"{self.__class__.__name__}({args_str})"
