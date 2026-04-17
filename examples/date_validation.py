"""
Date validation examples.

Covers the five date rules: date, before, after, date_equals, date_format.

Note: date, before, after, and date_equals accept only unambiguous ISO 8601
formats (YYYY-MM-DD, YYYY/MM/DD, and datetime variants). For regional
formats like DD-MM-YYYY, use date_format with an explicit format string.
"""

from nitro_validator import Validator, ValidationError


def example_basic_date():
    """Valid ISO 8601 dates pass the date rule."""
    print("=== Basic Date Validation ===\n")

    validator = Validator()

    data = {"birthdate": "1990-06-15", "joined_at": "2024-01-10T09:30:00"}
    rules = {"birthdate": "required|date", "joined_at": "required|date"}

    try:
        validated = validator.validate(data, rules)
        print("✓ ISO 8601 dates accepted!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.errors}\n")


def example_ambiguous_format_rejected():
    """Regional formats are rejected by the date rule."""
    print("=== Ambiguous Format Rejection ===\n")

    validator = Validator()

    # DD-MM-YYYY and MM-DD-YYYY are indistinguishable — the date rule rejects both
    data = {"event_date": "15-06-1990"}
    rules = {"event_date": "required|date"}

    try:
        validator.validate(data, rules)
        print("✓ Passed (unexpected!)")
    except ValidationError as e:
        print("✗ Rejected as expected (use date_format for regional formats):")
        print(f"  Errors: {e.errors}\n")


def example_before_after():
    """Compare a date against a reference date."""
    print("=== Before / After ===\n")

    validator = Validator()

    data = {
        "start_date": "2024-03-01",
        "end_date": "2024-12-31",
    }
    rules = {
        "start_date": "required|date|after:2024-01-01",
        "end_date": "required|date|before:2025-01-01",
    }

    try:
        validated = validator.validate(data, rules)
        print("✓ Date range valid!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.errors}\n")


def example_date_equals():
    """Require an exact date match."""
    print("=== Date Equals ===\n")

    validator = Validator()

    data = {"launch_date": "2025-07-04"}
    rules = {"launch_date": "required|date_equals:2025-07-04"}

    try:
        validator.validate(data, rules)
        print("✓ Date matches expected value!\n")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.errors}\n")


def example_date_format():
    """Use date_format for regional or non-ISO formats."""
    print("=== Date Format (Regional) ===\n")

    validator = Validator()

    data = {
        "uk_date": "15/06/1990",           # DD/MM/YYYY
        "us_date": "06-15-1990",           # MM-DD-YYYY
        "timestamp": "15 Jun 1990 09:30",  # DD Mon YYYY HH:MM
    }
    rules = {
        "uk_date": "required|date_format:%d/%m/%Y",
        "us_date": "required|date_format:%m-%d-%Y",
        "timestamp": "required|date_format:%d %b %Y %H:%M",
    }

    try:
        validated = validator.validate(data, rules)
        print("✓ All regional formats parsed!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.errors}\n")


if __name__ == "__main__":
    example_basic_date()
    example_ambiguous_format_rejected()
    example_before_after()
    example_date_equals()
    example_date_format()
