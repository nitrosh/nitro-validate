# Nitro Validate

Check incoming data against rules like `'required|email'` and get every error back at once, keyed by field. 51 built-in rules, custom rules in a few lines, and no dependencies.

[![PyPI](https://img.shields.io/pypi/v/nitro-validator?color=green)](https://pypi.org/project/nitro-validator/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nitro-validator)](https://pypi.org/project/nitro-validator/)
[![PyPI - License](https://img.shields.io/pypi/l/nitro-validator)](https://pypi.org/project/nitro-validator/)
[![image](https://img.shields.io/github/actions/workflow/status/nitrosh/nitro-validate/test.yml?branch=main)](https://github.com/nitrosh/nitro-validate/actions?query=branch%3Amain)

## Installation

```bash
pip install nitro-validator
```

Needs Python 3.7 or newer.

### AI assistant integration

Teach your AI coding assistant the rule names and API:

```bash
npx skills add nitrosh/nitro-validate
```

Assistants that support skills, like Claude Code, will then write validation code that uses the right rules.

## Quick Start

```python
from nitro_validator import NitroValidator, NitroValidationError

validator = NitroValidator()

data = {
    'email': 'user@example.com',
    'age': 25,
    'password': 'secret123',
    'confirm_password': 'secret123'
}

rules = {
    'email': 'required|email',
    'age': 'required|numeric|min:18',
    'password': 'required|min:8',
    'confirm_password': 'required|same:password'
}

try:
    validated_data = validator.validate(data, rules)
    print("Valid:", validated_data)
except NitroValidationError as e:
    print("Invalid:", e.errors)
```

Every rule runs for every field, so a bad payload reports all its problems in one go:

```python
{'email': ['The email field must be a valid email address.'],
 'age': ['The age field must be at least 18.']}
```

Every class has a shorter alias: `Validator`, `ValidationError`, `Rule` and `RuleRegistry`. The examples below use both.

## Why Nitro Validator?

- No runtime dependencies, so it drops into any project.
- 51 built-in rules for strings, numbers, dates, formats and cross-field checks.
- A custom rule is one small class with a name, a message and a `validate()` method.
- Error messages can be overridden per field or per rule.
- 100% test coverage.

## Available Rules

### Basic Rules

| Rule       | Description                         | Example                     |
|------------|-------------------------------------|-----------------------------|
| `required` | Field must be present and not empty | `'email': 'required'`       |
| `optional` | Field is optional (always passes)   | `'middle_name': 'optional'` |

Most other rules pass when the value is missing or empty, so `'email'` on its own accepts a blank field. Add `required` when the field has to be there.

### String Rules

| Rule              | Description                           | Example                      |
|-------------------|---------------------------------------|------------------------------|
| `alpha`           | Only alphabetic characters            | `'name': 'alpha'`            |
| `alphanumeric`    | Only alphanumeric characters          | `'username': 'alphanumeric'` |
| `alpha_dash`      | Letters, numbers, dashes, underscores | `'slug': 'alpha_dash'`       |
| `lowercase`       | Only lowercase characters             | `'code': 'lowercase'`        |
| `uppercase`       | Only uppercase characters             | `'code': 'uppercase'`        |
| `email`           | Valid email address                   | `'email': 'email'`           |
| `url`             | Valid http/https URL                  | `'website': 'url'`           |
| `uuid`            | UUID in 8-4-4-4-12 form               | `'id': 'uuid'`               |
| `ip`              | Valid IP address (v4 or v6)           | `'address': 'ip'`            |
| `ipv4`            | Valid IPv4 address                    | `'address': 'ipv4'`          |
| `ipv6`            | Valid IPv6 address                    | `'address': 'ipv6'`          |
| `json`            | Valid JSON string                     | `'data': 'json'`             |
| `slug`            | Valid URL slug                        | `'slug': 'slug'`             |
| `ascii`           | Only ASCII characters                 | `'text': 'ascii'`            |
| `base64`          | Valid base64 encoding                 | `'encoded': 'base64'`        |
| `hex_color`       | Valid hex color code                  | `'color': 'hex_color'`       |
| `credit_card`     | Valid credit card number              | `'card': 'credit_card'`      |
| `mac_address`     | Valid MAC address                     | `'mac': 'mac_address'`       |
| `timezone`        | IANA timezone name                    | `'tz': 'timezone'`           |
| `locale`          | Valid locale code                     | `'locale': 'locale'`         |
| `regex:pattern`   | Matches regex pattern                 | `'code': 'regex:^[A-Z]{3}$'` |
| `starts_with:str` | Starts with substring                 | `'name': 'starts_with:Mr'`   |
| `ends_with:str`   | Ends with substring                   | `'file': 'ends_with:.pdf'`   |
| `contains:str`    | Contains substring                    | `'text': 'contains:hello'`   |

A few of these are stricter than you might expect:

- Format rules check the whole value, so `"a@b.co\n"` fails `email`.
- `url` accepts http and https only. The host can be any domain, `localhost`, an IPv4 address or a bracketed IPv6 address, with an optional port from 1 to 65535.
- `timezone` wants an IANA name like `America/New_York`. It checks the real zone list when Python has one (3.9+ with system tz data or the `tzdata` package), and only checks the shape otherwise. Offsets like `+02:00` always fail.
- `regex` patterns containing `|` or `,` clash with the rule syntax, so pass them as an object: `RegexRule(r'^(a|b)$')`. A pattern that won't compile raises `InvalidRuleError`.

### Numeric Rules

| Rule              | Description             | Example                    |
|-------------------|-------------------------|----------------------------|
| `numeric`         | Must be numeric         | `'price': 'numeric'`       |
| `integer`         | Must be an integer      | `'quantity': 'integer'`    |
| `positive`        | Must be positive number | `'amount': 'positive'`     |
| `negative`        | Must be negative number | `'deficit': 'negative'`    |
| `min:value`       | Minimum value or length | `'age': 'min:18'`          |
| `max:value`       | Maximum value or length | `'rating': 'max:5'`        |
| `between:min,max` | Between two values      | `'score': 'between:0,100'` |
| `divisible_by:n`  | Divisible by number     | `'even': 'divisible_by:2'` |

Numbers can be ints, floats, or numeric strings like `"42"`, `"-1.5"` and `"1e3"`. `"nan"`, `"inf"`, `"1_000"` and padded strings like `" 42"` are rejected.

`min`, `max`, `between` and `size` compare numbers by value, and strings, lists and dicts by length. Add `numeric` or `integer` to the field and numeric strings are compared by value too, which is what you want for form input:

```python
validator.is_valid({'age': '25'}, {'age': 'numeric|min:18'})  # True, compares 25 >= 18
validator.is_valid({'name': '25'}, {'name': 'min:18'})        # False, compares len('25') >= 18
```

### Comparison Rules

| Rule               | Description                    | Example                               |
|--------------------|--------------------------------|---------------------------------------|
| `same:field`       | Must match another field       | `'password_confirm': 'same:password'` |
| `different:field`  | Must differ from another field | `'new_email': 'different:old_email'`  |
| `in:val1,val2`     | Must be in list of values      | `'role': 'in:admin,user,guest'`       |
| `not_in:val1,val2` | Must not be in list            | `'status': 'not_in:banned,deleted'`   |

### Boolean Rules

| Rule       | Description              | Example                  |
|------------|--------------------------|--------------------------|
| `boolean`  | Must be a boolean value  | `'active': 'boolean'`    |

### Date Rules

| Rule               | Description            | Example                             |
|--------------------|------------------------|-------------------------------------|
| `date`             | Must be a valid date   | `'birthdate': 'date'`               |
| `before:date`      | Date must be before    | `'start': 'before:2025-12-31'`      |
| `after:date`       | Date must be after     | `'end': 'after:2024-01-01'`         |
| `date_equals:date` | Date must equal        | `'today': 'date_equals:2024-11-23'` |
| `date_format:fmt`  | Date must match format | `'date': 'date_format:%Y-%m-%d'`    |

`date`, `before`, `after` and `date_equals` accept `date` and `datetime` objects, and ISO 8601 strings like `2024-01-31`, `2024/01/31` and `2024-01-31T14:30:00`. Fractional seconds and a `Z` or `+02:00` offset are fine too, so JavaScript's `toISOString()` output works. Times with an offset are converted to UTC before comparing, and times without one are treated as UTC.

Regional formats are rejected because they're ambiguous: is `01-02-2024` the 1st of February or January 2nd? If you need one, spell out the format with `date_format`, for example `'date_format:%d-%m-%Y'`.

### Convenience Rules

| Rule        | Description                       | Example                   |
|-------------|-----------------------------------|---------------------------|
| `confirmed` | Matches {field}_confirmation      | `'password': 'confirmed'` |
| `accepted`  | Must be accepted (yes/true/1/on)  | `'terms': 'accepted'`     |
| `declined`  | Must be declined (no/false/0/off) | `'marketing': 'declined'` |

### Length Rules

| Rule           | Description         | Example                     |
|----------------|---------------------|-----------------------------|
| `length:value` | Exact length        | `'zip_code': 'length:5'`    |

### Collection Rules

| Rule       | Description                        | Example                     |
|------------|------------------------------------|-----------------------------|
| `array`    | Must be a list or tuple            | `'items': 'array'`          |
| `size:n`   | Exact size (value or length)       | `'tags': 'size:3'`          |
| `distinct` | Array must have unique values      | `'ids': 'distinct'`         |

## Usage Examples

### Basic Validation

```python
from nitro_validator import NitroValidator, NitroValidationError

validator = NitroValidator()

data = {'username': 'johndoe', 'age': '25'}
rules = {'username': 'required|alphanumeric', 'age': 'required|integer|min:18'}

try:
    validated = validator.validate(data, rules)
    print(validated)  # {'username': 'johndoe', 'age': '25'}
except NitroValidationError as e:
    print(e.errors)
```

### Custom Error Messages

```python
# One message for every rule on a field
messages = {
    'email': 'Please provide a valid email address'
}

# Or a message per rule
messages = {
    'password': {
        'required': 'Password is required',
        'min': 'Password must be at least 8 characters'
    }
}

validator.validate(data, rules, messages)
```

### Using Rule Objects

```python
from nitro_validator import Validator, RequiredRule, EmailRule, MinRule

validator = Validator()

data = {'email': 'test@example.com', 'age': 25}
rules = {
    'email': [RequiredRule(), EmailRule()],
    'age': [RequiredRule(), MinRule(18)]
}

validated = validator.validate(data, rules)
```

Rules that don't take arguments can be passed as classes too: `[RequiredRule, EmailRule]`. Anything in the list that isn't a rule string, instance or class raises `InvalidRuleError`.

Rule arguments are checked when the rule is built. A missing or malformed argument like `'min:abc'`, `'between:1'` or `'before:not-a-date'` raises `InvalidRuleError` the first time the rules run, instead of quietly failing every value.

### Checking Without Exceptions

```python
validator = Validator()

if validator.is_valid(data, rules):
    print("Data is valid")
else:
    print("Errors:", validator.get_errors())
```

### Validate in One Call

```python
from nitro_validator import Validator, ValidationError

try:
    validator = Validator.make(data, rules)
    print("Valid:", validator.validated_data)
except ValidationError as e:
    print("Errors:", e.errors)
```

## Creating Custom Rules

A custom rule subclasses `NitroValidationRule` and sets a `name`, a `message` and a `validate()` method. Return `True` for empty values, so the rule only kicks in when the field has something in it:

```python
from typing import Any

from nitro_validator import NitroValidationRule, NitroValidator

class StrongPasswordRule(NitroValidationRule):
    name = "strong_password"
    message = "The {field} must contain uppercase, lowercase, numbers, and symbols."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if not value:
            return True

        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        has_digit = any(c.isdigit() for c in value)
        has_symbol = any(c in '!@#$%^&*()_+-=' for c in value)

        return has_upper and has_lower and has_digit and has_symbol


validator = NitroValidator()
validator.register_rule(StrongPasswordRule)

data = {'password': 'MyP@ssw0rd!'}
rules = {'password': 'required|strong_password'}

validated = validator.validate(data, rules)
```

If your rule takes arguments, set `min_args`, and building it with fewer raises `InvalidRuleError`. Arguments from a rule string like `'multiple_of:5'` arrive as strings, so cast them:

```python
class MultipleOfRule(NitroValidationRule):
    name = "multiple_of"
    message = "The {field} must be a multiple of {0}."
    min_args = 1

    def validate(self, field, value, data):
        if value is None or value == "":
            return True
        return isinstance(value, int) and value % int(self.args[0]) == 0
```

## Advanced Usage

### Cross-field Validation

```python
data = {
    'password': 'secret123',
    'password_confirmation': 'secret123'
}

rules = {
    'password': 'required|min:8',
    'password_confirmation': 'required|same:password'
}

validator.validate(data, rules)
```

### Conditional Validation

```python
# Only require an email from customers
data = {'user_type': 'customer', 'email': 'user@example.com'}

if data.get('user_type') == 'customer':
    rules = {'email': 'required|email'}
else:
    rules = {'email': 'optional'}

validator.validate(data, rules)
```

### Handling Validation Errors

```python
from nitro_validator import ValidationError

try:
    validator.validate(data, rules)
except ValidationError as e:
    # Errors keyed by field
    print(e.errors)  # {'email': ['Email is required'], 'age': ['Age must be at least 18']}

    # Or every message in one list
    flat_errors = validator.get_errors_flat()
    print(flat_errors)  # ['Email is required', 'Age must be at least 18']
```

`validator.errors` and `validator.validated_data` always hold the results of the most recent call. If one validator is shared between threads, read results from the return value and `e.errors` instead, or give each thread its own `Validator()`.

### Custom Rule Registry

Each `Validator()` gets its own copy of the built-in rules, so `register_rule()` on one validator never affects another. To build a registry yourself, start from an empty `RuleRegistry()` and add the built-ins back if you want them:

```python
from nitro_validator import Validator, RuleRegistry, register_builtin_rules

registry = RuleRegistry()
register_builtin_rules(registry)
registry.register(StrongPasswordRule)

validator = Validator(registry=registry)
```

## Examples

Runnable scripts live in `examples/`:

```bash
python examples/basic_usage.py
python examples/custom_rules.py
python examples/advanced_validation.py
python examples/date_validation.py
python examples/formats.py
```

## Development

### Setup

```bash
git clone https://github.com/nitrosh/nitro-validate.git
cd nitro-validate
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

The coverage report is included in every run.

### Format Code

```bash
black nitro_validator tests examples
```

## Coming from GUMP

Nitro Validator grew out of [GUMP](https://github.com/Wixel/GUMP), a PHP validation library by the same author, so the rule syntax will feel familiar. What's different:

- Custom rules are Python classes you register by name.
- Failures raise `ValidationError` with every error attached, or call `is_valid()` if you'd rather not catch anything.
- Type hints throughout.
- No dependencies, where GUMP needs PHP extensions.

## Ecosystem

- **[nitro-cli](https://github.com/nitrosh/nitro-cli)**: Static site generator that builds sites with Python code
- **[nitro-ui](https://github.com/nitrosh/nitro-ui)**: Build HTML with Python, not strings
- **[nitro-datastore](https://github.com/nitrosh/nitro-datastore)**: Schema-free JSON data store with dot notation access
- **[nitro-dispatch](https://github.com/nitrosh/nitro-dispatch)**: Framework-agnostic plugin system
- **[nitro-image](https://github.com/nitrosh/nitro-image)**: Fast, friendly image processing for the web

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for details.
