"""Regression tests for fixes from the 2026-10 code review.

Each class pins one issue from the review so the fix can't quietly regress.
"""

import sys
import threading
from datetime import date, datetime, timedelta, timezone

import pytest

from nitro_validator import (
    NitroInvalidRuleError,
    NitroValidationError,
    NitroValidationRule,
    Validator,
)
from nitro_validator.utils import (
    AfterRule,
    AlphaDashRule,
    BeforeRule,
    BetweenRule,
    DateEqualsRule,
    DateRule,
    DivisibleByRule,
    EmailRule,
    HexColorRule,
    InRule,
    IntegerRule,
    IpRule,
    Ipv4Rule,
    Ipv6Rule,
    LengthRule,
    LocaleRule,
    MacAddressRule,
    MaxRule,
    MinRule,
    NegativeRule,
    NotInRule,
    NumericRule,
    PositiveRule,
    RequiredRule,
    SlugRule,
    UrlRule,
    UuidRule,
)
from nitro_validator.utils.rules import _parse_iso_date, _to_number


class TestRuleClassesInRuleLists:
    """#1: rule classes are instantiated, anything else is rejected."""

    def test_rule_class_is_run(self):
        validator = Validator()
        assert validator.is_valid({}, {"email": [RequiredRule]}) is False
        assert validator.get_errors() == {"email": ["The email field is required."]}

    def test_rule_class_mixed_with_strings_and_instances(self):
        validator = Validator()
        rules = {"email": [RequiredRule, EmailRule(), "max:50"]}
        assert validator.validate({"email": "a@b.co"}, rules) == {"email": "a@b.co"}
        assert validator.is_valid({"email": "nope"}, rules) is False

    def test_non_rule_class_is_rejected(self):
        with pytest.raises(NitroInvalidRuleError, match="unsupported rule"):
            Validator().validate({"x": 1}, {"x": [int]})

    def test_rule_class_needing_args_raises(self):
        with pytest.raises(NitroInvalidRuleError):
            Validator().validate({"x": 1}, {"x": [MinRule]})


class TestFullMatchPatterns:
    """#2: a trailing newline must not slip past ``$``."""

    @pytest.mark.parametrize(
        "rule, valid",
        [
            (EmailRule(), "user@example.com"),
            (SlugRule(), "my-post"),
            (AlphaDashRule(), "user_name-1"),
            (HexColorRule(), "#ffaa00"),
            (MacAddressRule(), "AA:BB:CC:DD:EE:FF"),
            (MacAddressRule(), "AABBCCDDEEFF"),
            (LocaleRule(), "en_US"),
            (UrlRule(), "https://example.com/path"),
            (UuidRule(), "123e4567-e89b-12d3-a456-426614174000"),
            (IpRule(), "10.0.0.1"),
            (IpRule(), "::1"),
            (Ipv4Rule(), "192.168.1.1"),
            (Ipv6Rule(), "2001:db8::1"),
        ],
    )
    def test_trailing_newline_rejected(self, rule, valid):
        assert rule.validate("f", valid, {}) is True
        assert rule.validate("f", valid + "\n", {}) is False

    def test_email_via_validator(self):
        assert Validator().is_valid({"e": "a@b.co\n"}, {"e": "email"}) is False


class TestTimezoneAwareDates:
    """#3: aware and naive datetimes compare without crashing."""

    def test_aware_datetime_against_naive_arg(self):
        rule = BeforeRule("2999-01-01")
        assert rule.validate("d", datetime.now(timezone.utc), {}) is True

    def test_aware_arg_against_naive_value(self):
        rule = AfterRule(datetime(2024, 1, 1, tzinfo=timezone.utc))
        assert rule.validate("d", "2024-06-01", {}) is True

    def test_offsets_are_normalised_to_utc(self):
        plus_two = timezone(timedelta(hours=2))
        assert _parse_iso_date(datetime(2024, 1, 1, 12, tzinfo=plus_two)) == datetime(
            2024, 1, 1, 10
        )
        assert _parse_iso_date("2024-01-01T12:00:00+02:00") == datetime(2024, 1, 1, 10)

    def test_z_suffix_is_utc(self):
        assert _parse_iso_date("2024-01-01T10:00:00Z") == datetime(2024, 1, 1, 10)

    def test_same_instant_in_different_offsets(self):
        rule = DateEqualsRule("2024-01-01T10:00:00Z")
        assert rule.validate("d", "2024-01-01T12:00:00+02:00", {}) is True

    def test_after_with_offset_string(self):
        rule = AfterRule("2024-01-01T10:00:00Z")
        assert rule.validate("d", "2024-01-01T11:30:00+01:00", {}) is True
        assert rule.validate("d", "2024-01-01T10:30:00+01:00", {}) is False

    def test_validator_no_longer_raises_type_error(self):
        data = {"d": datetime.now(timezone.utc)}
        assert Validator().is_valid(data, {"d": "before:2999-01-01|after:2000-01-01"}) is True


class TestRuleArgumentValidation:
    """#4: bad rule arguments raise NitroInvalidRuleError when the rule is built."""

    @pytest.mark.parametrize(
        "rule_string",
        [
            "min:abc",
            "max:abc",
            "between:1,abc",
            "between:abc,1",
            "size:abc",
            "length:x",
            "length:3.5",
            "divisible_by:x",
            "divisible_by:0",
            "min:nan",
            "max:inf",
            "before:not-a-date",
            "after:31-12-2024",
            "date_equals:tomorrow",
            "regex:[unclosed",
        ],
    )
    def test_bad_argument_raises(self, rule_string):
        with pytest.raises(NitroInvalidRuleError):
            Validator().validate({"f": "x"}, {"f": rule_string})

    @pytest.mark.parametrize(
        "rule_string",
        [
            "min",
            "max",
            "between:1",
            "size",
            "length",
            "divisible_by",
            "same",
            "different",
            "in",
            "not_in",
            "regex",
            "starts_with",
            "ends_with",
            "contains",
            "before",
            "after",
            "date_equals",
            "date_format",
        ],
    )
    def test_missing_argument_raises(self, rule_string):
        with pytest.raises(NitroInvalidRuleError, match="needs at least"):
            Validator().validate({"f": "x"}, {"f": rule_string})

    def test_error_names_the_rule(self):
        with pytest.raises(NitroInvalidRuleError, match="'min'.*'abc'"):
            MinRule("abc")

    def test_custom_rule_min_args(self):
        class NeedsTwo(NitroValidationRule):
            name = "needs_two"
            min_args = 2

            def validate(self, field, value, data):
                return True

        with pytest.raises(NitroInvalidRuleError, match="'needs_two' needs at least 2"):
            NeedsTwo("a")
        assert NeedsTwo("a", "b").args == ("a", "b")

    def test_unnamed_custom_rule_uses_class_name(self):
        class Unnamed(NitroValidationRule):
            min_args = 1

        with pytest.raises(NitroInvalidRuleError, match="'Unnamed'"):
            Unnamed()

    def test_numeric_args_accepted_in_object_form(self):
        assert MinRule(18).limit == 18
        assert MinRule("1.5").limit == 1.5
        assert MinRule("-3").limit == -3
        assert BetweenRule("1", "1e2").upper == 100.0
        assert LengthRule("4").target == 4


class TestNumericContextForSizeRules:
    """#5: numeric strings are compared by value when the field is numeric."""

    def test_form_string_passes_numeric_min(self):
        validator = Validator()
        assert validator.is_valid({"age": "25"}, {"age": "required|numeric|min:18"}) is True
        assert validator.is_valid({"age": "12"}, {"age": "required|numeric|min:18"}) is False

    def test_rule_order_does_not_matter(self):
        assert Validator().is_valid({"age": "25"}, {"age": "min:18|integer"}) is True

    @pytest.mark.parametrize(
        "rules, value, expected",
        [
            ("integer|max:10", "9", True),
            ("integer|max:10", "11", False),
            ("numeric|between:1,5", "4.5", True),
            ("numeric|between:1,5", "5.5", False),
            ("numeric|size:3", "3", True),
            ("numeric|size:3", "abc", False),
            ("numeric|min:1", [1, 2], False),
        ],
    )
    def test_numeric_context(self, rules, value, expected):
        assert Validator().is_valid({"n": value}, {"n": rules}) is expected

    def test_numeric_context_with_rule_objects(self):
        rules = {"n": [NumericRule(), MinRule(18)]}
        assert Validator().is_valid({"n": "25"}, rules) is True

    def test_without_numeric_strings_are_measured_by_length(self):
        validator = Validator()
        assert validator.is_valid({"name": "25"}, {"name": "min:18"}) is False
        assert validator.is_valid({"name": "x" * 18}, {"name": "min:18"}) is True

    def test_shared_rule_instance_is_not_mutated(self):
        shared = MinRule(3)
        validator = Validator()
        assert validator.is_valid({"n": "10"}, {"n": [NumericRule(), shared]}) is True
        assert shared.numeric is False
        assert validator.is_valid({"s": "10"}, {"s": [shared]}) is False

    def test_as_numeric_default_returns_self(self):
        rule = EmailRule()
        assert rule.as_numeric() is rule

    def test_only_numeric_and_integer_imply_numeric(self):
        assert NumericRule.implies_numeric is True
        assert IntegerRule.implies_numeric is True
        assert MinRule.implies_numeric is False
        assert NitroValidationRule.implies_numeric is False


class TestIsoDateFormats:
    """#6: real-world ISO 8601 strings and date objects are accepted."""

    @pytest.mark.parametrize(
        "value",
        [
            "2024-01-01",
            "2024/01/01",
            "2024-01-01 10:00:00",
            "2024/01/01 10:00:00",
            "2024-01-01T10:00:00",
            "2024-01-01T10:00:00.123",
            "2024-01-01T10:00:00.000Z",
            "2024-01-01T10:00:00Z",
            "2024-01-01T10:00:00+02:00",
            "2024-01-01T10:00:00-0530",
            date(2024, 1, 1),
            datetime(2024, 1, 1, 10),
        ],
    )
    def test_accepted(self, value):
        assert DateRule().validate("d", value, {}) is True

    @pytest.mark.parametrize(
        "value", ["01-01-2024", "2024-01-01\n", "2024-13-01", "yesterday", 20240101, [2024]]
    )
    def test_rejected(self, value):
        assert DateRule().validate("d", value, {}) is False

    def test_date_object_is_midnight(self):
        assert _parse_iso_date(date(2024, 5, 6)) == datetime(2024, 5, 6)

    def test_date_object_as_rule_argument(self):
        assert BeforeRule(date(2024, 1, 2)).validate("d", "2024-01-01", {}) is True


class TestNumberParsing:
    """#7: nan, inf, underscores and padded strings are not numbers."""

    @pytest.mark.parametrize(
        "value",
        [
            "nan",
            "NaN",
            "inf",
            "-inf",
            "Infinity",
            "1_000",
            " 12",
            "12 ",
            "1e999",
            "",
            "1.2.3",
            "٣",
            True,
            float("nan"),
            float("inf"),
            [1],
            None,
        ],
    )
    def test_not_a_number(self, value):
        assert _to_number(value) is None

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("42", 42),
            ("-7", -7),
            ("+3", 3),
            ("1.5", 1.5),
            (".5", 0.5),
            ("5.", 5.0),
            ("1e3", 1000.0),
            ("2E-2", 0.02),
            (10, 10),
            (2.5, 2.5),
        ],
    )
    def test_numbers(self, value, expected):
        assert _to_number(value) == expected

    def test_integer_strings_stay_ints(self):
        assert isinstance(_to_number("123"), int)

    @pytest.mark.skipif(
        not hasattr(sys, "set_int_max_str_digits"), reason="int digit limit is 3.11+"
    )
    def test_oversized_integer_string(self):
        assert _to_number("1" * 5000) is None

    @pytest.mark.parametrize("value", ["nan", "inf", "1_000", float("nan"), float("inf")])
    def test_numeric_rule_rejects(self, value):
        assert NumericRule().validate("n", value, {}) is False

    @pytest.mark.parametrize("value", ["1_000", "1.0", "1e3", " 5", 5.0])
    def test_integer_rule_rejects(self, value):
        assert IntegerRule().validate("n", value, {}) is False

    def test_positive_and_negative_reject_infinity(self):
        assert PositiveRule().validate("n", "inf", {}) is False
        assert NegativeRule().validate("n", "-inf", {}) is False
        assert PositiveRule().validate("n", "0.1", {}) is True
        assert NegativeRule().validate("n", "-0.1", {}) is True

    def test_size_rules_reject_non_finite_numbers(self):
        assert MinRule(1).validate("n", float("inf"), {}) is False
        assert MaxRule(1).validate("n", float("nan"), {}) is False


class TestUrlRule:
    """#8: long TLDs, IP octets, IPv6 hosts and ports."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://nitro.photography",
            "https://example.international/path?q=1",
            "http://xn--e1afmkfd.xn--p1ai",
            "http://localhost:8000",
            "http://127.0.0.1",
            "http://255.255.255.255:65535/",
            "http://[::1]",
            "https://[2001:db8::1]:8443/path",
            "https://example.com/#fragment",
            "https://example.com.",
            "https://example.com?q=1",
        ],
    )
    def test_valid(self, url):
        assert UrlRule().validate("u", url, {}) is True

    @pytest.mark.parametrize(
        "url",
        [
            "http://999.999.999.999",
            "http://256.1.1.1",
            "http://[not:an:ip:zz]",
            "http://[1.2.3]",
            "http://example.com:0",
            "http://example.com:70000",
            "https://example.c",
            "https://example.com/has space",
            "ftp://example.com",
        ],
    )
    def test_invalid(self, url):
        assert UrlRule().validate("u", url, {}) is False


class TestUuidRule:
    """#9: only canonical 8-4-4-4-12 UUIDs are accepted."""

    @pytest.mark.parametrize(
        "value",
        [
            "{123e4567-e89b-12d3-a456-426614174000}",
            "urn:uuid:123e4567-e89b-12d3-a456-426614174000",
            "123e4567e89b12d3a456426614174000",
            "123e4567-e89b-12d3-a456-42661417400",
            "g23e4567-e89b-12d3-a456-426614174000",
        ],
    )
    def test_non_canonical_rejected(self, value):
        assert UuidRule().validate("u", value, {}) is False

    def test_uppercase_accepted(self):
        assert UuidRule().validate("u", "123E4567-E89B-12D3-A456-426614174000", {}) is True


class TestThreadSafety:
    """#11: custom messages don't mutate shared rules, results don't leak between calls."""

    def test_override_message_does_not_touch_rule(self):
        shared = RequiredRule()
        validator = Validator()
        validator.is_valid({}, {"name": [shared]}, {"name": "Custom"})
        assert shared.custom_message is None
        assert validator.get_errors() == {"name": ["Custom"]}

    def test_override_dict_for_other_rule_is_ignored(self):
        validator = Validator()
        validator.is_valid({}, {"name": "required"}, {"name": {"email": "Nope"}})
        assert validator.get_errors() == {"name": ["The name field is required."]}

    def test_non_string_override_is_ignored(self):
        validator = Validator()
        validator.is_valid({}, {"name": "required"}, {"name": 42})
        assert validator.get_errors() == {"name": ["The name field is required."]}

    def test_exception_errors_belong_to_their_call(self):
        validator = Validator()
        with pytest.raises(NitroValidationError) as first:
            validator.validate({}, {"a": "required"})
        validator.validate({"b": "x"}, {"b": "required"})
        assert first.value.errors == {"a": ["The a field is required."]}
        assert validator.get_errors() == {}

    def test_shared_rule_with_concurrent_custom_messages(self):
        shared = RequiredRule()
        seen = []

        def worker(message):
            for _ in range(200):
                try:
                    Validator().validate({}, {"f": [shared]}, {"f": message})
                except NitroValidationError as error:
                    seen.append((message, error.errors["f"][0]))

        threads = [threading.Thread(target=worker, args=(m,)) for m in ("one", "two")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert all(message == rendered for message, rendered in seen)
        assert shared.custom_message is None


class TestRegexRuleConfigErrors:
    """#12: an invalid pattern is a configuration error, not a failed value."""

    def test_invalid_pattern_raises(self):
        from nitro_validator.utils import RegexRule

        with pytest.raises(NitroInvalidRuleError, match="invalid pattern"):
            RegexRule("(")


class TestDivisibleByPrecision:
    """#13: integers use exact arithmetic, floats use decimal."""

    def test_large_integers(self):
        rule = DivisibleByRule("3")
        assert rule.validate("n", 10**20 + 1, {}) is False
        assert rule.validate("n", 10**20 + 2, {}) is True
        assert rule.validate("n", str(10**20 + 2), {}) is True

    def test_decimal_fractions(self):
        assert DivisibleByRule("0.1").validate("n", 0.3, {}) is True
        assert DivisibleByRule("0.1").validate("n", "1.0", {}) is True
        assert DivisibleByRule("0.25").validate("n", 1.3, {}) is False
        assert DivisibleByRule(2).validate("n", 4.0, {}) is True
        assert DivisibleByRule(2).validate("n", 5.0, {}) is False

    def test_negative_values(self):
        assert DivisibleByRule(3).validate("n", -9, {}) is True
        assert DivisibleByRule("-3").validate("n", 9, {}) is True

    def test_rejects_non_numbers(self):
        rule = DivisibleByRule(2)
        assert rule.validate("n", "abc", {}) is False
        assert rule.validate("n", True, {}) is False
        assert rule.validate("n", "inf", {}) is False

    def test_out_of_decimal_range_is_rejected(self):
        assert DivisibleByRule("0.1").validate("n", 1e300, {}) is False


class TestInRuleStillMatchesNumbers:
    """InRule/NotInRule keep matching ints against string args after the arg-count change."""

    def test_in_and_not_in(self):
        assert InRule("1", "2").validate("n", 2, {}) is True
        assert NotInRule("1", "2").validate("n", 3, {}) is True
