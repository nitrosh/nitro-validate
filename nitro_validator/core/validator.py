"""
Main NitroValidator class for validating data.
"""

import copy
from typing import Dict, Any, List, Sequence, Type, Union, Optional
from .rule import NitroValidationRule
from .rule_registry import NitroRuleRegistry
from .exceptions import NitroValidationError, NitroInvalidRuleError

RuleSpec = Union[str, Sequence[Union[str, NitroValidationRule, Type[NitroValidationRule]]]]


class NitroValidator:
    """Validate a data dict against a per-field rule spec.

    The validator resolves rule names through a :class:`NitroRuleRegistry`,
    runs every rule for every field, aggregates errors by field, and
    either returns the validated subset or raises
    :class:`NitroValidationError`.

    Rules can be expressed two ways, interchangeably within the same
    call:

    * Pipe-delimited strings: ``"required|email"``, ``"min:18"``,
      ``"between:1,100"``. Colon separates the rule name from its
      arguments; commas separate multiple arguments.
    * Rule instances or classes: ``[RequiredRule(), EmailRule]``.

    If a field has ``numeric`` or ``integer``, its ``min``, ``max``,
    ``between`` and ``size`` rules compare numeric strings by value, so
    ``"25"`` passes ``"numeric|min:18"``. Without them, strings are
    measured by length.

    Every :meth:`validate` call replaces :attr:`errors` and
    :attr:`validated_data`, so a validator can be reused for sequential
    calls. Those attributes always reflect the most recent call, so don't
    read them from a validator shared between threads. Use the return
    value and the raised exception's ``errors`` instead, or give each
    thread its own validator.

    Example:
        >>> from nitro_validator import NitroValidator
        >>> validator = NitroValidator()
        >>> validator.validate(
        ...     {'email': 'user@example.com', 'age': 25},
        ...     {'email': 'required|email', 'age': 'required|integer|min:18'},
        ... )
        {'email': 'user@example.com', 'age': 25}
    """

    def __init__(self, registry: Optional[NitroRuleRegistry] = None):
        """Create a validator backed by ``registry`` (or a fresh empty one).

        When imported from the top-level :mod:`nitro_validator` package,
        the default registry already contains every built-in rule.

        Args:
            registry: A :class:`NitroRuleRegistry` to resolve rule names
                against. Omit to use the default registry populated with
                built-in rules.
        """
        self.registry = registry or NitroRuleRegistry()
        self.errors: Dict[str, List[str]] = {}
        self.validated_data: Dict[str, Any] = {}

    def register_rule(
        self,
        rule_class: type,
        name: Optional[str] = None,
    ) -> "NitroValidator":
        """Register a custom rule class on this validator's registry.

        Args:
            rule_class: A :class:`NitroValidationRule` subclass.
            name: Optional override for the rule name.

        Returns:
            Self, to allow chaining.

        Example:
            >>> validator = NitroValidator().register_rule(StrongPasswordRule)
        """
        self.registry.register(rule_class, name)
        return self

    def validate(
        self,
        data: Dict[str, Any],
        rules: Dict[str, RuleSpec],
        messages: Optional[Dict[str, Union[str, Dict[str, str]]]] = None,
    ) -> Dict[str, Any]:
        """Run every rule for every field and return the validated data.

        Every rule for every field is evaluated before this method
        raises, so :attr:`errors` contains *all* failures, not just the
        first. Fields absent from ``data`` are validated against their
        rules with a value of ``None``. Most rules pass on ``None``, so
        pair with ``required`` to enforce presence.

        Args:
            data: The payload to validate.
            rules: Per-field rules. Values may be pipe-delimited strings
                (``"required|email"``) or lists mixing rule strings, rule
                instances, and rule classes.
            messages: Optional custom error messages. Each value is
                either a single string applied to all rules on that
                field, or a dict keyed by rule name for per-rule
                overrides.

        Returns:
            The subset of ``data`` whose fields passed every rule.

        Raises:
            NitroValidationError: If any field failed any rule; the
                exception's ``errors`` attribute holds the full report.
            NitroRuleNotFoundError: If a rule string names an unknown rule.
            NitroInvalidRuleError: If a rule has bad arguments, or a rule
                list contains something that isn't a rule.

        Example:
            >>> validator.validate(
            ...     {'email': 'test@example.com'},
            ...     {'email': 'required|email'},
            ... )
            {'email': 'test@example.com'}
        """
        errors: Dict[str, List[str]] = {}
        validated_data: Dict[str, Any] = {}
        messages = messages or {}

        for field, field_rules in rules.items():
            value = data.get(field)
            field_errors = []

            for rule in self._resolve_rules(field, field_rules):
                if not rule.validate(field, value, data):
                    field_errors.append(self._message_for(rule, field, messages.get(field)))

            if field_errors:
                errors[field] = field_errors
            else:
                validated_data[field] = value

        self.errors = errors
        self.validated_data = validated_data

        if errors:
            raise NitroValidationError(errors)

        return validated_data

    def _resolve_rules(
        self,
        field: str,
        field_rules: RuleSpec,
    ) -> List[NitroValidationRule]:
        """Turn a field's rule spec into rule instances, ready to run."""
        rule_list = self._parse_rules(field_rules) if isinstance(field_rules, str) else field_rules

        resolved = []
        for rule in rule_list:
            if isinstance(rule, str):
                resolved.append(self._create_rule_from_string(rule))
            elif isinstance(rule, NitroValidationRule):
                resolved.append(rule)
            elif isinstance(rule, type) and issubclass(rule, NitroValidationRule):
                resolved.append(rule())
            else:
                raise NitroInvalidRuleError(
                    f"Field '{field}' has an unsupported rule {rule!r}. Use a rule "
                    "string, a NitroValidationRule instance, or a NitroValidationRule "
                    "subclass."
                )

        if any(rule.implies_numeric for rule in resolved):
            resolved = [rule.as_numeric() for rule in resolved]

        return resolved

    def _message_for(
        self,
        rule: NitroValidationRule,
        field: str,
        override: Union[str, Dict[str, str], None],
    ) -> str:
        """Render a failing rule's message, applying any caller override."""
        if isinstance(override, dict):
            override = override.get(rule.name or rule.__class__.__name__.lower())
        if isinstance(override, str):
            rule = copy.copy(rule)
            rule.custom_message = override
        return rule.get_message(field)

    def is_valid(
        self,
        data: Dict[str, Any],
        rules: Dict[str, RuleSpec],
        messages: Optional[Dict[str, Union[str, Dict[str, str]]]] = None,
    ) -> bool:
        """Return ``True`` if ``data`` satisfies ``rules``, without raising.

        Wraps :meth:`validate` and swallows :class:`NitroValidationError`.
        On failure call :meth:`get_errors` to inspect the result.

        Args:
            data: The payload to validate.
            rules: Per-field rules (same format as :meth:`validate`).
            messages: Optional custom error messages.

        Returns:
            ``True`` if every field passed every rule, ``False`` otherwise.

        Example:
            >>> if not validator.is_valid(data, rules):
            ...     print(validator.get_errors())
        """
        try:
            self.validate(data, rules, messages)
            return True
        except NitroValidationError:
            return False

    def get_errors(self) -> Dict[str, List[str]]:
        """Return the errors from the most recent :meth:`validate` call.

        Returns:
            A dict mapping field name to the list of error messages
            accumulated for that field. Empty when the last validation
            succeeded.
        """
        return self.errors

    def get_errors_flat(self) -> List[str]:
        """Return every error message as a flat list, unkeyed by field.

        Preserves the insertion order from :attr:`errors`. Useful when
        surfacing validation failures as a single bullet list in a UI.

        Returns:
            A flat list of every error message across every field.
        """
        flat_errors = []
        for field_errors in self.errors.values():
            flat_errors.extend(field_errors)
        return flat_errors

    def _parse_rules(self, rules_string: str) -> List[str]:
        """
        Parse a pipe-delimited rule string.

        Args:
            rules_string: String like "required|email|min:5"

        Returns:
            List of rule strings
        """
        return [rule.strip() for rule in rules_string.split("|") if rule.strip()]

    def _create_rule_from_string(self, rule_string: str) -> NitroValidationRule:
        """
        Create a NitroValidationRule instance from a string.

        Args:
            rule_string: String like "min:5" or "required"

        Returns:
            NitroValidationRule instance

        Raises:
            NitroRuleNotFoundError: If the rule is not found.
            NitroInvalidRuleError: If the rule's constructor rejects the
                arguments (too few, or not the type it expects).

        Note:
            The pipe and comma are used to split rules and arguments
            respectively, so they cannot appear in rule arguments. Rules
            that need patterns containing ``|`` or ``,`` (notably
            ``regex``) must be passed as a rule instance instead of a
            string, e.g. ``RegexRule(r"^(a|b)$")``.
        """
        if ":" in rule_string:
            rule_name, args_string = rule_string.split(":", 1)
            args = [arg.strip() for arg in args_string.split(",")]
        else:
            rule_name = rule_string
            args = []

        rule_class = self.registry.get(rule_name)

        return rule_class(*args)

    @classmethod
    def make(
        cls,
        data: Dict[str, Any],
        rules: Dict[str, RuleSpec],
        messages: Optional[Dict[str, Union[str, Dict[str, str]]]] = None,
        registry: Optional[NitroRuleRegistry] = None,
    ) -> "NitroValidator":
        """Construct a validator and run :meth:`validate` in one call.

        Convenient when you only want a one-shot validation and the
        validator instance afterwards, e.g. to read
        :attr:`validated_data`.

        Args:
            data: The payload to validate.
            rules: Per-field rules (same format as :meth:`validate`).
            messages: Optional custom error messages.
            registry: Optional custom :class:`NitroRuleRegistry`.

        Returns:
            The validator instance, with :attr:`validated_data` populated.

        Raises:
            NitroValidationError: If validation fails.

        Example:
            >>> validator = NitroValidator.make(
            ...     {'email': 'a@b.co'}, {'email': 'required|email'},
            ... )
            >>> validator.validated_data
            {'email': 'a@b.co'}
        """
        validator = cls(registry)
        validator.validate(data, rules, messages)
        return validator
