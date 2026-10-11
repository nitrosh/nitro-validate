"""Regression tests for fixes from the 2026-05 code review.

Each test pins a specific bug or design issue identified during review so
the fix cannot silently regress.
"""

import pytest
from nitro_validator import (
    Validator,
    NitroValidationRule,
    NitroRuleRegistry,
    NitroInvalidRuleError,
    ValidationError,
)
from nitro_validator.utils import rules as rules_module
from nitro_validator.utils import (
    RegexRule,
    DateFormatRule,
    ConfirmedRule,
    NumericRule,
    IntegerRule,
    MinRule,
    MaxRule,
    BetweenRule,
    PositiveRule,
    NegativeRule,
    DivisibleByRule,
    SizeRule,
    InRule,
    NotInRule,
    EmailRule,
    TimezoneRule,
)


class TestRegexRuleSafe:
    """A malformed regex is a configuration error, raised when the rule is built."""

    def test_malformed_pattern_raises_invalid_rule_error(self):
        with pytest.raises(NitroInvalidRuleError, match="invalid pattern"):
            RegexRule("[unclosed")

    def test_malformed_pattern_via_validator_raises(self):
        validator = Validator()
        with pytest.raises(NitroInvalidRuleError):
            validator.is_valid({"x": "abc"}, {"x": "regex:(*invalid"})

    def test_non_string_pattern_raises(self):
        with pytest.raises(NitroInvalidRuleError):
            RegexRule(123)

    def test_pattern_compiled_once(self):
        rule = RegexRule(r"^\d+$")
        assert rule._compiled is not None
        first = rule._compiled
        rule.validate("f", "123", {})
        rule.validate("f", "456", {})
        assert rule._compiled is first


class TestRegistryIsolation:
    """Registering a rule on one validator must not leak to others (#3)."""

    def test_register_rule_does_not_pollute_default_registry(self):
        class ScratchRule(NitroValidationRule):
            name = "scratch_review"

            def validate(self, field, value, data):
                return True

        v1 = Validator()
        v1.register_rule(ScratchRule)
        assert v1.registry.has("scratch_review")

        v2 = Validator()
        assert v2.registry.has("scratch_review") is False

    def test_two_validators_have_distinct_registries(self):
        a = Validator()
        b = Validator()
        assert a.registry is not b.registry

    def test_explicit_registry_is_used_as_is(self):
        custom = NitroRuleRegistry()
        v = Validator(registry=custom)
        assert v.registry is custom

    def test_registry_copy_is_independent(self):
        a = NitroRuleRegistry()
        a.register(EmailRule)
        b = a.copy()
        assert b.has("email")
        b.unregister("email")
        assert a.has("email")
        assert b.has("email") is False


class TestDateFormatRuleSafe:
    """DateFormatRule must not leak re.error from bad format strings (#4)."""

    def test_duplicate_directive_returns_false_not_exception(self):
        rule = DateFormatRule("%Y%Y")
        assert rule.validate("d", "20262026", {}) is False

    def test_garbage_format_returns_false(self):
        rule = DateFormatRule("not a real format")
        assert rule.validate("d", "anything", {}) is False


class TestTimezoneRuleFallbackPath:
    """Exercise the structural fallback used when no tz database exists."""

    def test_fallback_used_when_no_zone_database(self, monkeypatch):
        monkeypatch.setattr(rules_module, "_iana_zones", lambda: None)

        rule = TimezoneRule()
        assert rule.validate("tz", "America/New_York", {}) is True
        assert rule.validate("tz", "invalid-timezone", {}) is False
        assert rule.validate("tz", "+02:00", {}) is False

    def test_iana_zones_none_without_zoneinfo(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def deny_zoneinfo(name, *args, **kwargs):
            if name == "zoneinfo":
                raise ImportError("zoneinfo not available")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", deny_zoneinfo)
        assert rules_module._iana_zones.__wrapped__() is None

    def test_iana_zones_none_when_database_empty(self, monkeypatch):
        zoneinfo = pytest.importorskip("zoneinfo")
        monkeypatch.setattr(zoneinfo, "available_timezones", lambda: set())
        assert rules_module._iana_zones.__wrapped__() is None

    def test_iana_zones_lists_real_zones(self, monkeypatch):
        zoneinfo = pytest.importorskip("zoneinfo")
        monkeypatch.setattr(zoneinfo, "available_timezones", lambda: {"Africa/Johannesburg"})
        assert rules_module._iana_zones.__wrapped__() == frozenset({"Africa/Johannesburg"})

    def test_database_path_rejects_offsets(self, monkeypatch):
        monkeypatch.setattr(rules_module, "_iana_zones", lambda: frozenset({"UTC"}))
        rule = TimezoneRule()
        assert rule.validate("tz", "UTC", {}) is True
        assert rule.validate("tz", "+02:00", {}) is False


class TestTimezoneRuleFallback:
    """The fallback regex must cover real IANA zone shapes (#5)."""

    @pytest.mark.parametrize(
        "zone",
        [
            "America/New_York",
            "US/Eastern",
            "Etc/UTC",
            "Etc/GMT+5",
            "Europe/London",
            "America/Argentina/Buenos_Aires",
            "Pacific/Honolulu",
            "UTC",
            "GMT",
        ],
    )
    def test_fallback_accepts_real_zones(self, zone):
        assert TimezoneRule._FALLBACK_PATTERN.fullmatch(zone) is not None

    @pytest.mark.parametrize(
        "junk",
        [
            "invalid-timezone",
            "123-456",
            "Not/A/Real/zone with spaces",
            "",
            "+02:00",
            "-0500",
            "UTC\n",
        ],
    )
    def test_fallback_rejects_junk(self, junk):
        assert TimezoneRule._FALLBACK_PATTERN.fullmatch(junk) is None


class TestInRuleNumericCoercion:
    """InRule must match numeric values against string-form args (#6)."""

    def test_int_matches_string_args(self):
        rule = InRule("1", "2", "3")
        assert rule.validate("n", 1, {}) is True
        assert rule.validate("n", 2, {}) is True
        assert rule.validate("n", 4, {}) is False

    def test_float_matches_string_args(self):
        rule = InRule("1.5", "2.5")
        assert rule.validate("n", 1.5, {}) is True
        assert rule.validate("n", 3.5, {}) is False

    def test_via_string_form(self):
        v = Validator()
        v.validate({"role": 1}, {"role": "in:1,2,3"})

    def test_not_in_rule_with_numeric(self):
        rule = NotInRule("1", "2", "3")
        assert rule.validate("n", 1, {}) is False
        assert rule.validate("n", 4, {}) is True

    def test_bool_not_treated_as_numeric(self):
        rule = InRule("1", "2")
        assert rule.validate("flag", True, {}) is False

    def test_non_numeric_string_arg_is_skipped(self):
        rule = InRule("abc", "2")
        assert rule.validate("n", 2, {}) is True

    def test_float_arg_matches_int_value(self):
        rule = InRule("abc", "2.0")
        assert rule.validate("n", 2, {}) is True

    def test_no_match_when_no_arg_coerces(self):
        rule = InRule("abc", "def")
        assert rule.validate("n", 2, {}) is False


class TestConfirmedRuleEmpty:
    """ConfirmedRule must skip empty values like every other non-presence rule (#9)."""

    def test_passes_on_none(self):
        rule = ConfirmedRule()
        assert rule.validate("password", None, {}) is True

    def test_passes_on_empty_string(self):
        rule = ConfirmedRule()
        assert rule.validate("password", "", {}) is True

    def test_still_fails_when_value_present_and_confirmation_missing(self):
        rule = ConfirmedRule()
        assert rule.validate("password", "secret", {}) is False

    def test_pair_with_required_enforces_presence(self):
        v = Validator()
        ok = v.is_valid({}, {"password": "required|confirmed"})
        assert ok is False


class TestNumericRulesExcludeBool:
    """Numeric rules should not silently accept bool (which subclasses int) (#10)."""

    def test_numeric_rejects_bool(self):
        rule = NumericRule()
        assert rule.validate("n", True, {}) is False
        assert rule.validate("n", False, {}) is False

    def test_min_rejects_bool(self):
        rule = MinRule("0")
        assert rule.validate("n", True, {}) is False

    def test_max_rejects_bool(self):
        rule = MaxRule("10")
        assert rule.validate("n", True, {}) is False

    def test_between_rejects_bool(self):
        rule = BetweenRule("0", "10")
        assert rule.validate("n", True, {}) is False

    def test_positive_rejects_bool(self):
        rule = PositiveRule()
        assert rule.validate("n", True, {}) is False

    def test_negative_rejects_bool(self):
        rule = NegativeRule()
        assert rule.validate("n", False, {}) is False

    def test_divisible_by_rejects_bool(self):
        rule = DivisibleByRule("2")
        assert rule.validate("n", True, {}) is False

    def test_size_rejects_bool(self):
        rule = SizeRule("1")
        assert rule.validate("n", True, {}) is False

    def test_integer_still_rejects_bool(self):
        rule = IntegerRule()
        assert rule.validate("n", True, {}) is False


class TestDivisibleByFloat:
    """DivisibleByRule must handle binary float artefacts (#11)."""

    def test_one_divided_by_point_one(self):
        rule = DivisibleByRule("0.1")
        assert rule.validate("n", 1.0, {}) is True

    def test_three_divided_by_point_three(self):
        rule = DivisibleByRule("0.3")
        assert rule.validate("n", 0.9, {}) is True

    def test_genuinely_indivisible_float(self):
        rule = DivisibleByRule("0.3")
        assert rule.validate("n", 1.0, {}) is False

    def test_integer_path_unchanged(self):
        rule = DivisibleByRule(2)
        assert rule.validate("n", 10, {}) is True
        assert rule.validate("n", 7, {}) is False


class TestCustomMessageDoesNotPersist:
    """Reusing a rule instance across calls must not retain prior custom messages (#12)."""

    def test_subsequent_call_without_messages_uses_default(self):
        rule = EmailRule()
        v = Validator()

        try:
            v.validate({"e": "junk"}, {"e": [rule]}, messages={"e": "custom oops"})
        except ValidationError as exc:
            assert exc.errors["e"] == ["custom oops"]

        try:
            v.validate({"e": "still junk"}, {"e": [rule]})
        except ValidationError as exc:
            assert exc.errors["e"] == ["The e field must be a valid email address."]

    def test_per_rule_override_then_default(self):
        rule = EmailRule()
        v = Validator()

        try:
            v.validate(
                {"e": "junk"},
                {"e": [rule]},
                messages={"e": {"email": "special email error"}},
            )
        except ValidationError as exc:
            assert exc.errors["e"] == ["special email error"]

        try:
            v.validate({"e": "junk"}, {"e": [rule]})
        except ValidationError as exc:
            assert exc.errors["e"] == ["The e field must be a valid email address."]


class TestRegexRuleDocBehaviour:
    """Sanity-check the documented workaround for pipe/comma in patterns (#2)."""

    def test_pattern_with_alternation_works_via_instance(self):
        rule = RegexRule(r"^(foo|bar)$")
        assert rule.validate("f", "foo", {}) is True
        assert rule.validate("f", "bar", {}) is True
        assert rule.validate("f", "baz", {}) is False
