# `fixed-width-int`

A robust implementation of fixed-width integers in Python that precisely emulates C-style behavior. Ideal for low-level programming, hardware emulation, and situations requiring exact control over integer representation and arithmetic.

## Features

- **C-like Behavior**:
  - Two's complement signed integers
  - Modular arithmetic for unsigned integers
  - Value wrapping on overflow/underflow
  - C-style division (truncates toward zero)
  - C-style modulo (matches division behavior)
  - Automatic type promotion
- **Type System**:
  - Dynamic type creation via bit-width parameterization (e.g., `Unsigned[8]`, `Signed[10]`)
  - Intuitive subtype relationships:
    - `Signed[m]` is a supertype of `Signed[n]` when m > n
    - `Unsigned[m]` is a supertype of `Unsigned[n]` when m > n
    - `Signed[m]` is a supertype of `Unsigned[n]` when m > n
  - Full support for `isinstance` and `issubclass` checks
- **Compatibility**
  - Pure Python
  - Supports Python 2+

## Installation

```bash
pip install fixed-width-int
```

## Quick Start

```python
from fixed_width_int import Unsigned, Signed

# Type definitions
U8 = Unsigned[8]   # 8-bit unsigned
S10 = Signed[10]   # 10-bit signed

# Basic operations
assert U8(255) + U8(1) == U8(0)        # Wraps around
assert S10(511) + S10(1) == S10(-512)  # Two's complement behavior

# Type promotion
assert type(U8(200) + S10(100)) is S10
assert U8(200) + S10(100) == S10(300)
```

## Comprehensive Examples

### Type System and Basic Operations

```python
from fixed_width_int import Unsigned, Signed

# Type definitions
U8 = Unsigned[8]
U16 = Unsigned[16]
S8 = Signed[8]
S16 = Signed[16]

# Subtyping checks
assert issubclass(U8, U16)      # Wider unsigned types are supertypes
assert issubclass(S8, S16)      # Wider signed types are supertypes
assert issubclass(U8, S16)      # Unsigned is subtype of wider signed
assert not issubclass(S8, U16)  # Signed isn't subtype of wider unsigned

# Value wrapping
assert U8(256) == U8(0)        # Modular arithmetic
assert S8(128) == S8(-128)     # Two's complement wrap
assert S8(-129) == S8(127)     # Underflow handling

# Addition/subtraction
assert U8(200) + U8(100) == U8(44)   # 300 % 256
assert S8(-100) - S8(30) == S8(126) # Wraps around

# Multiplication
assert U8(20) * U8(13) == U8(4)      # 260 % 256
assert S8(-10) * S8(13) == S8(126)  # -130 wraps to 126

# C-style division
assert S8(7) / S8(3) == S8(2)       # Truncates toward zero
assert S8(-7) / S8(3) == S8(-2)     # Negative division

# C-style modulo
assert S8(7) % S8(3) == S8(1)
assert S8(-7) % S8(3) == S8(-1)       # Matches division

# Basic bitwise ops
assert U8(0b10101010) & U8(0b11001100) == U8(0b10001000)
assert U8(0b10101010) | U8(0b11001100) == U8(0b11101110)

# Shifts
assert S8(0b11110000) >> S8(2) == S8(-4)   # Arithmetic right shift
assert U8(0b11110000) >> U8(2) == U8(0b00111100)  # Logical right shift
assert U8(1) << U8(7) == U8(128)
assert U8(1) << U8(8) == U8(0)

# Exponentiation
assert pow(U8(3), U8(4)) == U8(81)
assert pow(S8(2), S8(5), S8(9)) == S8(5)  # With modulus

# Type coercion and promotion

# Coerced to unsigned
assert type(U8(200) + S8(100)) is U8
assert U8(200) + S8(100) == U8(44)

# Promoted to wider signed
assert type(S16(-10) + U8(10)) is S16
assert S16(-10) + U8(10) == S16(0)

# Coerced to wider unsigned
assert type(U16(10) + S8(-11)) is U16
assert U16(10) + S8(-11) == U16(65535)

# Comparisons
assert S8(-1) == U8(255)           # Value equality
assert U8(255) > S8(0)             # Comparison works across types
assert U8(1) < S8(-1)              # Because S8(-1) gets coerced to U8(255)

# Negation, identity, absolute
assert -S8(5) == S8(-5)
assert +S8(-5) == S8(-5)
assert abs(S8(-5)) == S8(5)
assert abs(S8(-128)) == S8(-128)  # Overflow!
```

## Implementation Highlights

### Core Architecture

- **Metaclass Magic**: `FixedWidthIntMeta` dynamically creates fixed-width types while caching them for efficiency
- **Strict Type Safety**: Prevents direct instantiation of raw `Signed`/`Unsigned` without bit-width specification

### Key Components

1. **Metaclass `FixedWidthIntMeta`**:
   - Dynamically generates concrete integer types through `__getitem__`
   - Manages type caching
   - Sets width-specific properties (BIT_WIDTH, MODULO, etc.)

2. **Base Class `FixedWidthIntBase`**:
   - Implements all `numbers.Integral` abstract methods
   - Handles core arithmetic with proper wrapping behavior
   - Stores actual value in `promoted_to_int`

- **Signed and Unsigned Types**:
  - `Signed`: Implements two's complement behavior
  - `Unsigned`: Implements modular arithmetic behavior
  - Both implement `wrap_integral` to handle value truncation/interpretation
  - Both implement `__subclasshook__` to establish the subtype relationships described in the requirements
     - Carefully avoids infinite recursion

- **Preventing Direct Instantiation**:
  - `FixedWidthIntBase.__new__` checks if `cls.BIT_WIDTH == inf`
  - If true, raise an informative error telling users they must use `Signed[bit_width]` or `Unsigned[bit_width]` first
  - This prevents raw `Signed()` or `Unsigned()` instantiation

```python
from fixed_width_int import Signed


# This works for type checking
assert issubclass(Signed[8], Signed)
assert issubclass(Signed[8], Signed[8])
assert issubclass(Signed[8], Signed[9])

assert isinstance(Signed[8](42), Signed)
assert isinstance(Signed[8](42), Signed[8])
assert isinstance(Signed[8](42), Signed[9])

# Raises ValueError about needing to specify bitwidth
Signed(42)
```

## Why Use This Library?

- **Precision**: Get exactly the integer behavior you need for emulators, protocols, or low-level code
- **Safety**: Clear error messages and strict type checking prevent subtle bugs
- **Pythonic**: Integrates smoothly with Python's type system and number hierarchy
- **Performance**: Optimized implementation with minimal overhead

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
