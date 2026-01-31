# Nitro Validator

A dependency-free Python data validation library with 51+ built-in rules.

## Installation

```bash
pip install nitro-validator
```

## Quick Start

```python
from nitro_validator import NitroValidator, NitroValidationError

validator = NitroValidator()

data = {'email': 'user@example.com', 'age': 25}
rules = {'email': 'required|email', 'age': 'required|integer|min:18'}

try:
    validated = validator.validate(data, rules)
except NitroValidationError as e:
    print(e.errors)  # {'field': ['error message', ...]}
```

## Aliases

| Full Name | Alias |
|-----------|-------|
| `NitroValidator` | `Validator` |
| `NitroValidationRule` | `Rule` |
| `NitroValidationError` | `ValidationError` |
| `NitroRuleRegistry` | `RuleRegistry` |

## Rule Syntax

Rules are pipe-delimited strings with optional colon-separated arguments:

```python
'required'              # No arguments
'min:18'                # Single argument
'between:1,100'         # Multiple arguments
'in:admin,user,guest'   # List of values
```

## Available Rules

### Basic
| Rule | Description |
|------|-------------|
| `required` | Must be present and not empty |
| `optional` | Always passes (marks field optional) |

### String
| Rule | Description |
|------|-------------|
| `alpha` | Alphabetic characters only |
| `alphanumeric` | Alphanumeric characters only |
| `alpha_dash` | Letters, numbers, dashes, underscores |
| `lowercase` | Lowercase characters only |
| `uppercase` | Uppercase characters only |
| `email` | Valid email address |
| `url` | Valid URL |
| `uuid` | Valid UUID |
| `ip` | Valid IP address (v4 or v6) |
| `ipv4` | Valid IPv4 address |
| `ipv6` | Valid IPv6 address |
| `json` | Valid JSON string |
| `slug` | Valid URL slug |
| `ascii` | ASCII characters only |
| `base64` | Valid base64 encoding |
| `hex_color` | Valid hex color (#fff or #ffffff) |
| `credit_card` | Valid credit card (Luhn algorithm) |
| `mac_address` | Valid MAC address |
| `timezone` | Valid timezone identifier |
| `locale` | Valid locale code (en_US, pt_BR) |
| `regex:pattern` | Matches regex pattern |
| `starts_with:str` | Starts with substring |
| `ends_with:str` | Ends with substring |
| `contains:str` | Contains substring |

### Numeric
| Rule | Description |
|------|-------------|
| `numeric` | Numeric value (int, float, or numeric string) |
| `integer` | Integer value |
| `positive` | Positive number (> 0) |
| `negative` | Negative number (< 0) |
| `min:n` | Minimum value (numbers) or length (strings/arrays) |
| `max:n` | Maximum value (numbers) or length (strings/arrays) |
| `between:min,max` | Between two values (inclusive) |
| `divisible_by:n` | Divisible by number |

### Comparison
| Rule | Description |
|------|-------------|
| `same:field` | Must match another field's value |
| `different:field` | Must differ from another field's value |
| `in:val1,val2,...` | Must be one of the listed values |
| `not_in:val1,val2,...` | Must not be one of the listed values |

### Boolean
| Rule | Description |
|------|-------------|
| `boolean` | Boolean value (true/false, 1/0, yes/no, on/off) |

### Date
| Rule | Description |
|------|-------------|
| `date` | Valid date (ISO 8601 formats only: YYYY-MM-DD) |
| `before:date` | Date before the given date |
| `after:date` | Date after the given date |
| `date_equals:date` | Date equals the given date |
| `date_format:fmt` | Date matches specific format (e.g., `%Y-%m-%d`) |

**Note:** The `date`, `before`, `after`, and `date_equals` rules only accept ISO 8601 formats (`YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY-MM-DDTHH:MM:SS`). Use `date_format` for regional formats.

### Convenience
| Rule | Description |
|------|-------------|
| `confirmed` | Must match `{field}_confirmation` field |
| `accepted` | Must be accepted (true, yes, 1, on) |
| `declined` | Must be declined (false, no, 0, off) |

### Length/Size
| Rule | Description |
|------|-------------|
| `length:n` | Exact length (strings) or size (arrays) |
| `size:n` | Exact size/length/value |

### Collection
| Rule | Description |
|------|-------------|
| `array` | Must be a list or tuple |
| `distinct` | Array must contain unique values |

## Common Patterns

### Check validity without exception

```python
if validator.is_valid(data, rules):
    print("Valid!")
else:
    print(validator.get_errors())
```

### Custom error messages

```python
# Single message for all rules on a field
messages = {'email': 'Please enter a valid email'}

# Per-rule messages
messages = {
    'password': {
        'required': 'Password is required',
        'min': 'Password must be at least 8 characters'
    }
}

validator.validate(data, rules, messages)
```

### Using rule objects

```python
from nitro_validator import RequiredRule, EmailRule, MinRule

rules = {
    'email': [RequiredRule(), EmailRule()],
    'age': [RequiredRule(), MinRule(18)]
}
```

### Password confirmation

```python
data = {
    'password': 'secret123',
    'password_confirmation': 'secret123'
}
rules = {
    'password': 'required|min:8|confirmed'
}
```

### Factory method

```python
validator = NitroValidator.make(data, rules)  # Raises on failure
print(validator.validated_data)
```

## Creating Custom Rules

```python
from nitro_validator import NitroValidationRule, NitroValidator

class StrongPasswordRule(NitroValidationRule):
    name = "strong_password"
    message = "The {field} must contain uppercase, lowercase, numbers, and symbols."

    def validate(self, field: str, value, data: dict) -> bool:
        if not value:
            return True  # Let 'required' handle empty values

        return (
            any(c.isupper() for c in value) and
            any(c.islower() for c in value) and
            any(c.isdigit() for c in value) and
            any(c in '!@#$%^&*' for c in value)
        )

validator = NitroValidator()
validator.register_rule(StrongPasswordRule)
validator.validate(data, {'password': 'required|strong_password'})
```

## Error Handling

```python
try:
    validator.validate(data, rules)
except NitroValidationError as e:
    e.errors        # {'field': ['error1', 'error2'], ...}

# Or without exception
validator.is_valid(data, rules)
validator.get_errors()       # {'field': ['error1', ...]}
validator.get_errors_flat()  # ['error1', 'error2', ...]
```

## Key Points

- All rules pass for `None` or empty string except `required` and `accepted`/`declined`
- `min`/`max`/`between` check value for numbers, length for strings/arrays
- Date rules require ISO 8601 format; use `date_format` for other formats
- Custom rules should return `True` for empty values (let `required` handle presence)
