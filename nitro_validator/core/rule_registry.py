"""
Rule registry for managing validation rules.
"""

from typing import Dict, Type, Optional
from .rule import Rule
from .exceptions import RuleNotFoundError, InvalidRuleError


class RuleRegistry:
    """
    Registry for storing and retrieving validation rules.

    This allows users to register custom rules and access built-in rules.
    """

    def __init__(self):
        """Initialize the rule registry."""
        self._rules: Dict[str, Type[Rule]] = {}

    def register(self, rule_class: Type[Rule], name: Optional[str] = None):
        """
        Register a validation rule.

        Args:
            rule_class: The Rule class to register
            name: Optional custom name for the rule (defaults to rule_class.name)

        Raises:
            InvalidRuleError: If the rule class is invalid
        """
        if not issubclass(rule_class, Rule):
            raise InvalidRuleError(f"{rule_class} must inherit from Rule")

        rule_name = name or rule_class.name

        if not rule_name:
            raise InvalidRuleError(
                f"Rule {rule_class} must have a 'name' attribute or provide a name parameter"
            )

        self._rules[rule_name] = rule_class

    def unregister(self, name: str):
        """
        Unregister a validation rule.

        Args:
            name: The name of the rule to unregister
        """
        if name in self._rules:
            del self._rules[name]

    def get(self, name: str) -> Type[Rule]:
        """
        Get a rule class by name.

        Args:
            name: The name of the rule

        Returns:
            The Rule class

        Raises:
            RuleNotFoundError: If the rule is not found
        """
        if name not in self._rules:
            raise RuleNotFoundError(f"Rule '{name}' not found in registry")

        return self._rules[name]

    def has(self, name: str) -> bool:
        """
        Check if a rule exists in the registry.

        Args:
            name: The name of the rule

        Returns:
            True if the rule exists, False otherwise
        """
        return name in self._rules

    def all(self) -> Dict[str, Type[Rule]]:
        """
        Get all registered rules.

        Returns:
            Dictionary of rule names to Rule classes
        """
        return self._rules.copy()

    def clear(self):
        """Clear all registered rules."""
        self._rules.clear()
