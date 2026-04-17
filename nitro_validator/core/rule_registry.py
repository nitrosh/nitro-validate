"""
Rule registry for managing validation rules.
"""

from typing import Dict, Type, Optional
from .rule import NitroValidationRule
from .exceptions import NitroRuleNotFoundError, NitroInvalidRuleError


class NitroRuleRegistry:
    """Store and look up validation rule classes by name.

    Rule strings like ``"required|email"`` are resolved against a
    registry: each name is mapped to a :class:`NitroValidationRule`
    subclass, which the validator then instantiates. Each
    :class:`NitroValidator` has its own registry, pre-populated with the
    51+ built-in rules. Use this class directly when you want a
    container isolated from the default built-ins.

    Example:
        >>> from nitro_validator import NitroRuleRegistry, NitroValidator
        >>> registry = NitroRuleRegistry()
        >>> registry.register(MyCustomRule)
        >>> validator = NitroValidator(registry=registry)
    """

    def __init__(self) -> None:
        """Create an empty registry with no rules registered."""
        self._rules: Dict[str, Type[NitroValidationRule]] = {}

    def register(
        self,
        rule_class: Type[NitroValidationRule],
        name: Optional[str] = None,
    ) -> None:
        """Register a rule class under its ``name`` attribute or an override.

        Args:
            rule_class: A :class:`NitroValidationRule` subclass to add.
            name: Optional name override. Defaults to ``rule_class.name``.

        Raises:
            NitroInvalidRuleError: If ``rule_class`` does not subclass
                :class:`NitroValidationRule`, or if neither ``name`` nor
                ``rule_class.name`` is set.

        Example:
            >>> registry = NitroRuleRegistry()
            >>> registry.register(EmailRule)
            >>> registry.has("email")
            True
        """
        if not issubclass(rule_class, NitroValidationRule):
            raise NitroInvalidRuleError(f"{rule_class} must inherit from NitroValidationRule")

        rule_name = name or rule_class.name

        if not rule_name:
            raise NitroInvalidRuleError(
                f"Rule {rule_class} must have a 'name' attribute or provide a name parameter"
            )

        self._rules[rule_name] = rule_class

    def unregister(self, name: str) -> None:
        """Remove a rule from the registry. No-op if it is not registered.

        Args:
            name: The rule name to remove.

        Example:
            >>> registry.unregister("email")
            >>> registry.has("email")
            False
        """
        if name in self._rules:
            del self._rules[name]

    def get(self, name: str) -> Type[NitroValidationRule]:
        """Return the rule class registered under ``name``.

        Args:
            name: The rule name to look up.

        Returns:
            The :class:`NitroValidationRule` subclass registered for
            ``name``.

        Raises:
            NitroRuleNotFoundError: If no rule is registered under
                that name.

        Example:
            >>> registry.get("email") is EmailRule
            True
        """
        if name not in self._rules:
            raise NitroRuleNotFoundError(f"Rule '{name}' not found in registry")

        return self._rules[name]

    def has(self, name: str) -> bool:
        """Return ``True`` if a rule is registered under ``name``.

        Args:
            name: The rule name to check.

        Returns:
            ``True`` if ``name`` is registered, ``False`` otherwise.
        """
        return name in self._rules

    def all(self) -> Dict[str, Type[NitroValidationRule]]:
        """Return a shallow copy of the name-to-class mapping.

        The returned dict is detached from the registry, so mutating it
        does not affect registration.

        Returns:
            A fresh dict mapping each registered rule name to its class.
        """
        return self._rules.copy()

    def clear(self) -> None:
        """Remove every registered rule. Useful for building a registry from scratch."""
        self._rules.clear()
