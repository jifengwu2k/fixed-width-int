# Copyright (c) 2025 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
import abc
import sys
from numbers import Integral
from operator import add, and_, eq, le, lt, mul, lshift, or_, rshift, xor
from typing import Type, TypeVar, Callable

from six import with_metaclass

if sys.version_info < (3,):
    BigInt = long
else:
    BigInt = int

BIGINT_0 = BigInt(0)
BIGINT_1 = BigInt(1)
FLOAT_INF = float('inf')


def c_style_division(first, second):
    # type: (BigInt, BigInt) -> BigInt
    if (first >= BIGINT_0 and second >= BIGINT_0) or (first <= BIGINT_0 and second <= BIGINT_0):
        return first // second
    else:
        return first // second + BIGINT_1


def c_style_modulo(first, second):
    # type: (BigInt, BigInt) -> BigInt
    return first - c_style_division(first, second) * second


M = TypeVar('M', bound='FixedWidthIntMeta')


class FixedWidthIntMeta(abc.ABCMeta):
    """
    Metaclass for fixed-width integers.
    This metaclass handles dynamic type creation based on bit width.
    By using this metaclass in `Signed`, the expression `Signed[32]`,
    which calls `FixedWidthIntMeta.__getitem__(Signed, 32)`,
    would dynamically instantiate a **type** `Signed[32]`
    containing the class properties BIT_WIDTH, MODULO, SIGNED_MIN, SIGNED_MAX, UNSIGNED_MAX.
    This is reminiscent to what C++ does with Signed<32>
    given the class template <int BIT_WIDTH> class Signed
    """
    # Class properties in all fixed-width types
    # Set to comical default values
    # This makes checks like `issubclass(Signed[8], Signed)` work
    # While also serving as a guard lest the user tries to initialize the fixed-width types directly
    # Without setting `BIT_WIDTH` through dynamic subtyping
    BIT_WIDTH = FLOAT_INF  # type: BigInt
    MODULO = FLOAT_INF  # type: BigInt
    SIGNED_MIN = -FLOAT_INF  # type: BigInt
    SIGNED_MAX = FLOAT_INF  # type: BigInt
    UNSIGNED_MAX = FLOAT_INF  # type: BigInt

    _class_and_bit_width_to_instantiation = {}

    def __getitem__(self, bit_width):
        # type: (M, Integral) -> M
        bit_width = BigInt(bit_width)
        if bit_width <= BIGINT_1:
            raise ValueError('Bit width must be an integer greater than 1.')

        if (self, bit_width) in self._class_and_bit_width_to_instantiation:
            instantiation = self._class_and_bit_width_to_instantiation[(self, bit_width)]
        else:
            # Instantiate a new type object.
            # This is essentially a dynamic form of the class statement.
            modulo = BIGINT_1 << bit_width
            unsigned_max = (BIGINT_1 << bit_width) - BIGINT_1
            signed_min = -(BIGINT_1 << (bit_width - BIGINT_1))
            signed_max = (BIGINT_1 << (bit_width - BIGINT_1)) - BIGINT_1

            instantiation = type(
                '%s[%s]' % (self.__name__, bit_width),
                (self,),
                dict(
                    __module__=self.__module__,
                    BIT_WIDTH=bit_width,
                    MODULO=modulo,
                    UNSIGNED_MAX=unsigned_max,
                    SIGNED_MIN=signed_min,
                    SIGNED_MAX=signed_max
                )
            )

            self._class_and_bit_width_to_instantiation[(self, bit_width)] = instantiation

        return instantiation


B = TypeVar('B', bound='FixedWidthIntBase')


class FixedWidthIntBase(with_metaclass(FixedWidthIntMeta, Integral)):
    """
    Base class for fixed-width integers that emulate C behavior.
    Not meant to be instantiated directly - use FixedInt or UnsignedFixedInt.
    """
    __slots__ = ('promoted_to_bigint',)

    def __new__(cls, integral):
        # type: (Type[B], Integral) -> B
        if cls.BIT_WIDTH == FLOAT_INF:
            cls_name = cls.__name__
            raise ValueError(
                "Are you calling %s(...) directly? "
                "You should set bit width by dynamically subtyping through %s[BIT_WIDTH] first "
                "before calling its constructor: %s[BIT_WIDTH](...)" % (
                    cls_name, cls_name, cls_name
                )
            )

        instance = super(FixedWidthIntBase, cls).__new__(cls)
        instance.promoted_to_bigint = cls.wrap_integral(integral)
        return instance

    @classmethod
    def wrap_integral(cls, integral):
        # type: (Integral) -> BigInt
        raise NotImplementedError

    # class object:
    #     def __repr__(self) -> str: ...  # noqa: Y029
    def __repr__(self):
        # type: () -> str
        return '%s(%d)' % (type(self).__name__, self.promoted_to_bigint)

    # class object:
    #     def __str__(self) -> str: ...  # noqa: Y029
    def __str__(self):
        # type: () -> str
        return str(self.promoted_to_bigint)

    # class Number(metaclass=ABCMeta):
    #     @abstractmethod
    #     def __hash__(self) -> int: ...
    def __hash__(self):
        return hash(self.promoted_to_bigint)

    # class Real(Complex, _RealLike):
    #     @abstractmethod
    #     def __ceil__(self) -> _IntegralLike: ...
    def __ceil__(self):
        # type: () -> B
        return self

    # class Real(Complex, _RealLike):
    #     @abstractmethod
    #     def __floor__(self) -> _IntegralLike: ...
    def __floor__(self):
        # type: () -> B
        return self

    # class Real(Complex, _RealLike):
    #     @abstractmethod
    #     def __trunc__(self) -> _IntegralLike: ...
    def __trunc__(self):
        # type: () -> B
        return self

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __abs__(self) -> _IntegralLike: ...
    def __abs__(self):
        # type: () -> B
        new_instance = self.__class__(abs(self.promoted_to_bigint))
        return new_instance

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __int__(self) -> int: ...
    if sys.version_info < (3,):
        def __long__(self):
            return self.promoted_to_bigint

    def __int__(self):
        return self.promoted_to_bigint

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __invert__(self) -> _IntegralLike: ...
    def __invert__(self):
        # type: () -> B
        new_instance = self.__class__(~self.promoted_to_bigint)
        return new_instance

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __neg__(self) -> _IntegralLike: ...
    def __neg__(self):
        # type: () -> B
        new_instance = self.__class__(-self.promoted_to_bigint)
        return new_instance

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __pos__(self) -> _IntegralLike: ...
    def __pos__(self):
        # type: () -> B
        new_instance = self.__class__(+self.promoted_to_bigint)
        return new_instance

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     @overload
    #     def __round__(self, ndigits: None = None) -> _IntegralLike: ...
    #     @abstractmethod
    #     @overload
    #     def __round__(self, ndigits: int) -> _IntegralLike: ...
    def __round__(self, ndigits=None):
        return self

    # class Complex(Number, _ComplexLike):
    #     @abstractmethod
    #     def __add__(self, other) -> _ComplexLike: ...
    def __add__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(self, other, add)
        return NotImplemented

    # class Complex(Number, _ComplexLike):
    #     @abstractmethod
    #     def __radd__(self, other) -> _ComplexLike: ...
    def __radd__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, add)
        return NotImplemented

    # class Complex(Number, _ComplexLike):
    #     @abstractmethod
    #     def __eq__(self, other: object) -> bool: ...
    def __eq__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_comparison_operation(self, other, eq)
        return NotImplemented

    # class Complex(Number, _ComplexLike):
    #     @abstractmethod
    #     def __mul__(self, other) -> _ComplexLike: ...
    def __mul__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(self, other, mul)
        return NotImplemented

    # class Complex(Number, _ComplexLike):
    #     @abstractmethod
    #     def __rmul__(self, other) -> _ComplexLike: ...
    def __rmul__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, mul)
        return NotImplemented

    # class Complex(Number, _ComplexLike):
    #     @abstractmethod
    #     def __rpow__(self, base) -> _ComplexLike: ...
    def __rpow__(self, other):
        # other ** self
        # `self` MUST be non-negative for the operation to be closed on fixed-width integers
        if self.promoted_to_bigint >= 0 and isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, pow)
        return NotImplemented

    # class Complex(Number, _ComplexLike):
    #     @abstractmethod
    #     def __truediv__(self, other) -> _ComplexLike: ...
    # class Complex(Number, _ComplexLike):
    #     @abstractmethod
    #     def __rtruediv__(self, other) -> _ComplexLike: ...
    if sys.version_info < (3,):
        def __div__(self, other):
            # Performs C-style truncate toward zero floor division for the operation to be closed on fixed-width integers
            # `other` MUST be non-zero for the operation to be closed on fixed-width integers
            if isinstance(other, FixedWidthIntBase) and other.promoted_to_bigint != 0:
                return perform_binary_operation(self, other, c_style_division)
            return NotImplemented

        def __rdiv__(self, other):
            # Performs C-style truncate toward zero floor division for the operation to be closed on fixed-width integers
            # `self` MUST be non-zero for the operation to be closed on fixed-width integers
            if self.promoted_to_bigint != 0 and isinstance(other, FixedWidthIntBase):
                return perform_binary_operation(other, self, c_style_division)
            return NotImplemented

    def __truediv__(self, other):
        # Performs C-style truncate toward zero floor division for the operation to be closed on fixed-width integers
        # `other` MUST be non-zero for the operation to be closed on fixed-width integers
        if isinstance(other, FixedWidthIntBase) and other.promoted_to_bigint != 0:
            return perform_binary_operation(self, other, c_style_division)
        return NotImplemented

    def __rtruediv__(self, other):
        # Performs C-style truncate toward zero floor division for the operation to be closed on fixed-width integers
        # `self` MUST be non-zero for the operation to be closed on fixed-width integers
        if self.promoted_to_bigint != 0 and isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, c_style_division)
        return NotImplemented

    # class Real(Complex, _RealLike):
    #     @abstractmethod
    #     def __floordiv__(self, other) -> _RealLike: ...
    def __floordiv__(self, other):
        # Performs C-style truncate toward zero floor division
        # `other` MUST be non-zero for the operation to be closed on fixed-width integers
        if isinstance(other, FixedWidthIntBase) and other.promoted_to_bigint != 0:
            return perform_binary_operation(self, other, c_style_division)
        return NotImplemented

    # class Real(Complex, _RealLike):
    #     @abstractmethod
    #     def __rfloordiv__(self, other) -> _RealLike: ...
    def __rfloordiv__(self, other):
        # Performs C-style truncate toward zero floor division
        # `self` MUST be non-zero for the operation to be closed on fixed-width integers
        if self.promoted_to_bigint != 0 and isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, c_style_division)
        return NotImplemented

    # class Real(Complex, _RealLike):
    #     @abstractmethod
    #     def __le__(self, other) -> bool: ...
    def __le__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_comparison_operation(self, other, le)
        return NotImplemented

    # class Real(Complex, _RealLike):
    #     @abstractmethod
    #     def __lt__(self, other) -> bool: ...
    def __lt__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_comparison_operation(self, other, lt)
        return NotImplemented

    # class Real(Complex, _RealLike):
    #     @abstractmethod
    #     def __mod__(self, other) -> _RealLike: ...
    def __mod__(self, other):
        # Performs C-style modulo
        # `other` MUST be non-zero for the operation to be closed on fixed-width integers
        if isinstance(other, FixedWidthIntBase) and other.promoted_to_bigint != 0:
            return perform_binary_operation(self, other, c_style_modulo)
        return NotImplemented

    # class Real(Complex, _RealLike):
    #     @abstractmethod
    #     def __rmod__(self, other) -> _RealLike: ...
    def __rmod__(self, other):
        # Performs C-style modulo
        # `self` MUST be non-zero for the operation to be closed on fixed-width integers
        if self.promoted_to_bigint != 0 and isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, c_style_modulo)
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __and__(self, other) -> _IntegralLike: ...
    def __and__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(self, other, and_)
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __rand__(self, other) -> _IntegralLike: ...
    def __rand__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, and_)
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __lshift__(self, other) -> _IntegralLike: ...
    def __lshift__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(self, other, lshift)
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __rlshift__(self, other) -> _IntegralLike: ...
    def __rlshift__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, lshift)
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __or__(self, other) -> _IntegralLike: ...
    def __or__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(self, other, or_)
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __ror__(self, other) -> _IntegralLike: ...
    def __ror__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, or_)
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __pow__(self, exponent, modulus: Incomplete | None = None) -> _IntegralLike: ...
    def __pow__(self, exponent, modulus=None):
        # (self ** exponent) % modulus
        # `exponent` MUST be non-negative for the operation to be closed on fixed-width integers
        # `modulus` MUST be non-zero for the operation to be closed on fixed-width integers
        if isinstance(exponent, FixedWidthIntBase) and exponent.promoted_to_bigint >= 0:
            power_result = perform_binary_operation(self, exponent, pow)
            if modulus is None:
                return power_result
            if isinstance(modulus, FixedWidthIntBase) and modulus.promoted_to_bigint != 0:
                return power_result % modulus
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __rshift__(self, other) -> _IntegralLike: ...
    def __rshift__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(self, other, rshift)
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __rrshift__(self, other) -> _IntegralLike: ...
    def __rrshift__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, rshift)
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __xor__(self, other) -> _IntegralLike: ...
    def __xor__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(self, other, xor)
        return NotImplemented

    # class Integral(Rational, _IntegralLike):
    #     @abstractmethod
    #     def __rxor__(self, other) -> _IntegralLike: ...
    def __rxor__(self, other):
        if isinstance(other, FixedWidthIntBase):
            return perform_binary_operation(other, self, xor)
        return NotImplemented


S = TypeVar('S', bound='Signed')


class Signed(FixedWidthIntBase):
    """Signed fixed-width integer with two's complement behavior."""

    @classmethod
    def wrap_integral(cls, integral):
        # type: (Integral) -> BigInt
        truncated = BigInt(integral) & cls.UNSIGNED_MAX  # type: BigInt
        if truncated > cls.SIGNED_MAX:
            return truncated - cls.MODULO
        else:
            return truncated

    @classmethod
    def __subclasshook__(cls, __subclass):
        # type: (type) -> bool
        # If `n < m`, both `Signed[n]` and `Unsigned[n]` are subclasses of `Signed[m]`.
        # If `n == m`, `Signed[n]` is also a subclass of `Signed[m]`.
        # Here, `cls` is `Signed[m]`.

        # Is `__subclass` `Signed[n]` with `n <= m`?
        # Is `__subclass` `Unsigned[n]` with `n < m`?
        # NOTE: DO NOT USE `issubclass` HERE.
        # WE ARE IMPLEMENTING WHAT `issubclass` DOES.
        # USING `issubclass` WOULD LEAD TO INFINITE RECURSION.
        if (
                (Signed in __subclass.__mro__ and getattr(__subclass, 'BIT_WIDTH') <= cls.BIT_WIDTH)
                or (Unsigned in __subclass.__mro__ and getattr(__subclass, 'BIT_WIDTH') < cls.BIT_WIDTH)
        ):
            return True
        # In other cases, we retreat to the default check
        else:
            return NotImplemented


U = TypeVar('U', bound='Unsigned')


class Unsigned(FixedWidthIntBase):
    """Unsigned fixed-width integer with modular arithmetic behavior."""

    @classmethod
    def wrap_integral(cls, integral):
        # type: (Integral) -> BigInt
        truncated = BigInt(integral) & cls.UNSIGNED_MAX  # type: BigInt
        return truncated

    @classmethod
    def __subclasshook__(cls, __subclass):
        # type: (type) -> bool
        # If `n < m`, only `Unsigned[n]` is a subclass of `Unsigned[m]`.
        # If `n == m`, `Unsigned[n]` is also a subclass of `Unsigned[m]`.
        # Here, `cls` is `Unsigned[m]`.

        # Is `__subclass` `Unsigned[n]` with `n <= m`?
        # NOTE: DO NOT USE `issubclass` HERE.
        # WE ARE IMPLEMENTING WHAT `issubclass` DOES.
        # USING `issubclass` WOULD LEAD TO INFINITE RECURSION.
        if Unsigned in __subclass.__mro__ and getattr(__subclass, 'BIT_WIDTH') <= cls.BIT_WIDTH:
            return True
        # In other cases, we retreat to the default check
        else:
            return NotImplemented


def coerce(lhs, rhs):
    # type: (B, B) -> tuple[B, B, Type[B]]
    lhs_type = type(lhs)
    rhs_type = type(rhs)

    # Cases for `lhs_type` and `rhs_type`
    # Each can be `Unsigned[m]`, `Unsigned[n]`, `Signed[m]`, `Signed[n]`, `m > n`
    # A total of `4 x 4 = 16`

    # Same type
    # Do nothing
    # 4 cases
    if lhs_type is rhs_type:
        return lhs, rhs, lhs_type
    # Have common supertype
    # Safely convert subtype to supertype
    # 6 cases
    elif issubclass(lhs_type, rhs_type):
        return rhs_type(lhs), rhs, rhs_type
    elif issubclass(rhs_type, lhs_type):
        return lhs, lhs_type(rhs), lhs_type
    # Remaining cases (6 total)
    # `Unsigned[m]` `Signed[m]` or `Signed[m]` `Unsigned[m]`
    # `Unsigned[n]` `Signed[n]` or Signed[n]` `Unsigned[n]`
    # `Unsigned[m]` `Signed[n]` or `Signed[n]` `Unsigned[m]`
    # We follow C's conversion rules
    # 1. Same size? Convert `Signed` to `Unsigned`
    # 2. `Unsigned[m]` `Signed[n]` or `Signed[n]` `Unsigned[m]`? `Signed[n]` -> `Signed[m]` -> `Unsigned[m]`
    # Because `Signed[n]` -> `Signed[m]` is lossless, we can directly convert `Signed[n]` to `Unsigned[m]`
    else:
        # Which type is unsigned?
        if issubclass(lhs_type, Unsigned):
            return lhs, lhs_type(rhs), lhs_type
        else:
            return rhs_type(lhs), rhs, rhs_type


def perform_binary_operation(lhs, rhs, binary_operation):
    # type: (B, B, Callable[[BigInt, BigInt], BigInt]) -> B
    new_lhs, new_rhs, new_type = coerce(lhs, rhs)
    return new_type(binary_operation(new_lhs.promoted_to_bigint, new_rhs.promoted_to_bigint))


def perform_comparison_operation(lhs, rhs, comparison_operation):
    # type: (B, B, Callable[[BigInt, BigInt], bool]) -> bool
    new_lhs, new_rhs, _ = coerce(lhs, rhs)
    return comparison_operation(new_lhs.promoted_to_bigint, new_rhs.promoted_to_bigint)
