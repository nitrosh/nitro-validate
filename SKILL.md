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

Lists of rule objects and rule classes work too: `[RequiredRule, MinRule(18)]`. Bad or missing arguments (`'min:abc'`, `'between:1'`, a `regex` that won't compile) raise `NitroInvalidRuleError` when the rule is built. Patterns containing `|` or `,` must use `RegexRule(...)` directly.

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
| `url` | Valid http/https URL (any TLD, localhost, IPv4, bracketed IPv6, port 1-65535) |
| `uuid` | UUID in canonical 8-4-4-4-12 form |
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
| `timezone` | IANA timezone name (fixed offsets like `+02:00` are rejected) |
| `locale` | Valid locale code (en_US, pt_BR) |
| `regex:pattern` | Matches regex pattern |
| `starts_with:str` | Starts with substring |
| `ends_with:str` | Ends with substring |
| `contains:str` | Contains substring |

### Numeric
| Rule | Description |
|------|-------------|
| `numeric` | Finite int, float, or numeric string (rejects `nan`, `inf`, `1_000`) |
| `integer` | Integer value |
| `positive` | Positive number (> 0) |
| `negative` | Negative number (< 0) |
| `min:n` | Minimum value (numbers) or length (strings/arrays); see note below |
| `max:n` | Maximum value (numbers) or length (strings/arrays) |
| `between:min,max` | Between two values (inclusive) |
| `divisible_by:n` | Divisible by number |

**Note:** When a field also has `numeric` or `integer`, `min`, `max`, `between` and `size` compare numeric strings by value: `'numeric|min:18'` passes `"25"`. Without them, strings are measured by length.

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
| `date` | Valid date (`date`/`datetime` objects or ISO 8601 strings) |
| `before:date` | Date before the given date |
| `after:date` | Date after the given date |
| `date_equals:date` | Date equals the given date |
| `date_format:fmt` | Date matches specific format (e.g., `%Y-%m-%d`) |

**Note:** `date`, `before`, `after` and `date_equals` accept `date`/`datetime` objects and ISO 8601 strings (`YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY-MM-DDTHH:MM:SS` with optional fractional seconds and `Z` or `+HH:MM` offset). Offsets are converted to UTC before comparing; values without one are treated as UTC. Use `date_format` for regional formats.

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
| `size:n` | Exact value (numbers) or length (strings/arrays) |

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

Set `min_args = N` on a rule that needs arguments; building it with fewer raises `NitroInvalidRuleError`.

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
- `min`/`max`/`between`/`size` check value for numbers, length for strings/arrays, and value for numeric strings when the field has `numeric` or `integer`
- Date rules require ISO 8601 format; use `date_format` for other formats
- Format rules match the whole value; a trailing newline fails
- `validator.errors` reflects the last call only; don't read it from a validator shared across threads
- Custom rules should return `True` for empty values (let `required` handle presence)
- `RuleRegistry()` starts empty; call `register_builtin_rules(registry)` to add the built-ins
