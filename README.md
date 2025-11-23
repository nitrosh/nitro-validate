# Nitro Validator

A powerful, standalone, dependency-free data validation library for Python with extensible rules and a clean, intuitive API.

## Requirements

Python `3.7` or higher is required.

## Installation

```bash
pip install nitro-validator
```

## Features

- **Simple API** - Easy to learn with minimal boilerplate
- **Zero Dependencies** - No external dependencies required
- **Extensible** - Create custom validation rules with ease
- **Clean Syntax** - Pipe-delimited rule strings or rule objects
- **Custom Messages** - Override default error messages per field or rule
- **Cross-field Validation** - Validate fields against other fields
- **Type Safe** - Validates strings, numbers, booleans, dates, and more
- **Comprehensive Rules** - 18+ built-in validation rules

## Quick Start

```python
from nitro_validator import Validator

# Create a validator instance
validator = Validator()

# Define your data and rules
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

# Validate
try:
    validated_data = validator.validate(data, rules)
    print("Validation passed!", validated_data)
except ValidationError as e:
    print("Validation failed:", e.errors)
```

## Available Rules

### Basic Rules

| Rule       | Description                    | Example                  |
|------------|--------------------------------|--------------------------|
| `required` | Field must be present and not empty | `'email': 'required'` |
| `optional` | Field is optional (always passes) | `'middle_name': 'optional'` |

### String Rules

| Rule            | Description                        | Example                       |
|-----------------|------------------------------------|-------------------------------|
| `alpha`         | Only alphabetic characters         | `'name': 'alpha'`             |
| `alphanumeric`  | Only alphanumeric characters       | `'username': 'alphanumeric'`  |
| `email`         | Valid email address                | `'email': 'email'`            |
| `url`           | Valid URL                          | `'website': 'url'`            |
| `regex:pattern` | Matches regex pattern              | `'code': 'regex:^[A-Z]{3}$'`  |

### Numeric Rules

| Rule           | Description                    | Example                          |
|----------------|--------------------------------|----------------------------------|
| `numeric`      | Must be numeric                | `'price': 'numeric'`             |
| `integer`      | Must be an integer             | `'quantity': 'integer'`          |
| `min:value`    | Minimum value or length        | `'age': 'min:18'`                |
| `max:value`    | Maximum value or length        | `'rating': 'max:5'`              |
| `between:min,max` | Between two values          | `'score': 'between:0,100'`       |

### Comparison Rules

| Rule              | Description                  | Example                             |
|-------------------|------------------------------|-------------------------------------|
| `same:field`      | Must match another field     | `'password_confirm': 'same:password'` |
| `different:field` | Must differ from another field | `'new_email': 'different:old_email'` |
| `in:val1,val2`    | Must be in list of values    | `'role': 'in:admin,user,guest'`     |
| `not_in:val1,val2` | Must not be in list         | `'status': 'not_in:banned,deleted'` |

### Boolean Rules

| Rule       | Description              | Example                  |
|------------|--------------------------|--------------------------|
| `boolean`  | Must be a boolean value  | `'active': 'boolean'`    |

### Date Rules

| Rule   | Description           | Example                 |
|--------|-----------------------|-------------------------|
| `date` | Must be a valid date  | `'birthdate': 'date'`   |

### Length Rules

| Rule           | Description         | Example                     |
|----------------|---------------------|-----------------------------|
| `length:value` | Exact length        | `'zip_code': 'length:5'`    |

## Usage Examples

### Basic Validation

```python
from nitro_validator import Validator, ValidationError

validator = Validator()

data = {'username': 'john_doe', 'age': '25'}
rules = {'username': 'required|alphanumeric', 'age': 'required|integer|min:18'}

try:
    validated = validator.validate(data, rules)
    print(validated)  # {'username': 'john_doe', 'age': '25'}
except ValidationError as e:
    print(e.errors)
```

### Custom Error Messages

```python
# Single message for all rules on a field
messages = {
    'email': 'Please provide a valid email address'
}

# Or specific messages per rule
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

### Check Validation Without Exception

```python
validator = Validator()

if validator.is_valid(data, rules):
    print("Data is valid!")
else:
    print("Errors:", validator.get_errors())
```

### Static Factory Method

```python
from nitro_validator import Validator

# Create and validate in one call
try:
    validator = Validator.make(data, rules)
    print("Valid:", validator.validated_data)
except ValidationError as e:
    print("Errors:", e.errors)
```

## Creating Custom Rules

Extend the `Rule` class to create custom validation rules:

```python
from nitro_validator import Rule, Validator

class StrongPasswordRule(Rule):
    """Validate that a password is strong."""

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


# Register and use the custom rule
validator = Validator()
validator.register_rule(StrongPasswordRule)

data = {'password': 'MyP@ssw0rd!'}
rules = {'password': 'required|strong_password'}

validated = validator.validate(data, rules)
```

## Advanced Usage

### Cross-field Validation

```python
# Validate that one field matches another
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
# Validate email only if user type is 'customer'
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
    # Get all errors as a dictionary
    print(e.errors)  # {'email': ['Email is required'], 'age': ['Age must be at least 18']}

    # Or get flattened list of all error messages
    flat_errors = validator.get_errors_flat()
    print(flat_errors)  # ['Email is required', 'Age must be at least 18']
```

### Custom Rule Registry

```python
from nitro_validator import Validator, RuleRegistry

# Create a custom registry
registry = RuleRegistry()
registry.register(MyCustomRule)

# Use it with a validator
validator = Validator(registry=registry)
```

## Examples

The `examples/` directory contains working examples:

```bash
python examples/basic_usage.py
python examples/custom_rules.py
python examples/advanced_validation.py
```

## Development

### Setup

```bash
git clone https://github.com/nitro/nitro-validator.git
cd nitro-validator
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=nitro_validator
```

### Format Code

```bash
black nitro_validator tests examples
```

## Why Nitro Validator?

- **No Dependencies**: Unlike other validation libraries, Nitro Validator has zero external dependencies
- **Extensible**: Easy to create and register custom validation rules
- **Clean API**: Simple, intuitive syntax that's easy to learn and use
- **Pythonic**: Follows Python best practices and idioms
- **Well-tested**: Comprehensive test suite with high code coverage
- **Type-safe**: Works with strings, numbers, booleans, dates, and custom types

## Comparison with GUMP

Nitro Validator is inspired by [GUMP](https://github.com/Wixel/GUMP) (a PHP validation library) but redesigned for Python with:

- More Pythonic API and conventions
- Better extensibility with the Rule class system
- Cleaner error handling with custom exceptions
- Type hints and modern Python features
- No external dependencies (GUMP requires PHP extensions)

## License

Please see [LICENSE](LICENSE) for licensing details.

## Author

[github.com/sn](https://github.com/sn)
