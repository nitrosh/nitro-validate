"""
Format validation examples.

Covers identifier and format-string rules: uuid, url, ipv4, mac_address,
credit_card, hex_color, and regex.

Note: the string form splits on `|` (rules) and `,` (args). For regex
patterns containing those characters, pass a RegexRule object instead.
"""

from nitro_validator import Validator, ValidationError, RegexRule, RequiredRule


def example_identifiers():
    """UUID, URL, IPv4, and MAC address rules."""
    print("=== Identifiers (UUID, URL, IPv4, MAC) ===\n")

    validator = Validator()

    data = {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "website": "https://example.com/about",
        "server_ip": "192.168.1.42",
        "nic": "00:1B:44:11:3A:B7",
    }
    rules = {
        "request_id": "required|uuid",
        "website": "required|url",
        "server_ip": "required|ipv4",
        "nic": "required|mac_address",
    }

    try:
        validated = validator.validate(data, rules)
        print("✓ All identifiers valid!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.errors}\n")


def example_credit_card_and_color():
    """Credit card (Luhn-checked) and hex color codes."""
    print("=== Credit Card & Hex Color ===\n")

    validator = Validator()

    # 4532015112830366 is a Luhn-valid test number
    data = {
        "card": "4532015112830366",
        "brand_color": "#3366FF",
        "accent": "#f0a",
    }
    rules = {
        "card": "required|credit_card",
        "brand_color": "required|hex_color",
        "accent": "required|hex_color",
    }

    try:
        validated = validator.validate(data, rules)
        print("✓ Card number (Luhn) and colors valid!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.errors}\n")


def example_invalid_credit_card():
    """A number that fails the Luhn check is rejected."""
    print("=== Invalid Credit Card (Luhn Fail) ===\n")

    validator = Validator()

    data = {"card": "4532015112830367"}  # last digit altered — Luhn fails
    rules = {"card": "required|credit_card"}

    try:
        validator.validate(data, rules)
        print("✓ Passed (unexpected!)")
    except ValidationError as e:
        print("✗ Rejected as expected:")
        print(f"  Errors: {e.errors}\n")


def example_regex_string_form():
    """Simple regex via the pipe-string syntax (no `|` or `,` in pattern)."""
    print("=== Regex (String Form) ===\n")

    validator = Validator()

    # US zip code: 5 digits, optional -4 extension
    data = {"zip": "94103", "zip_plus_four": "94103-1234"}
    rules = {
        "zip": "required|regex:^\\d{5}$",
        "zip_plus_four": "required|regex:^\\d{5}-\\d{4}$",
    }

    try:
        validated = validator.validate(data, rules)
        print("✓ Both zip formats matched!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.errors}\n")


def example_regex_rule_object():
    """Use the RegexRule object when the pattern contains `|` or `,`."""
    print("=== Regex (Rule Object for Complex Patterns) ===\n")

    validator = Validator()

    # Pattern uses alternation (`|`) and a quantifier with a comma —
    # both would be mis-parsed by the string form.
    data = {"country_code": "GB", "postcode": "SW1A 1AA"}
    rules = {
        "country_code": [RequiredRule(), RegexRule(r"^(US|GB|CA|AU)$")],
        "postcode": [RequiredRule(), RegexRule(r"^[A-Z]{1,2}\d{1,2}[A-Z]? \d[A-Z]{2}$")],
    }

    try:
        validated = validator.validate(data, rules)
        print("✓ Complex patterns matched!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.errors}\n")


if __name__ == "__main__":
    example_identifiers()
    example_credit_card_and_color()
    example_invalid_credit_card()
    example_regex_string_form()
    example_regex_rule_object()
