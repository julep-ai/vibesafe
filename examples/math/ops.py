"""
Example defless functions for mathematical operations.
"""

from defless import defless, DeflessHandled


@defless.func
def sum_str(a: str, b: str) -> str:
    """
    Add two integers represented as strings.

    >>> sum_str("2", "3")
    '5'
    >>> sum_str("10", "20")
    '30'
    >>> sum_str("-5", "10")
    '5'
    """
    # Convert to ints for the AI to understand the context
    a_int, b_int = int(a), int(b)
    yield DeflessHandled()


@defless.func
def fibonacci(n: int) -> int:
    """
    Return the nth Fibonacci number (0-indexed).

    >>> fibonacci(0)
    0
    >>> fibonacci(1)
    1
    >>> fibonacci(5)
    5
    >>> fibonacci(10)
    55
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    yield DeflessHandled()


@defless.func
def is_prime(n: int) -> bool:
    """
    Check if a number is prime.

    >>> is_prime(2)
    True
    >>> is_prime(3)
    True
    >>> is_prime(4)
    False
    >>> is_prime(17)
    True
    >>> is_prime(1)
    False
    """
    if n < 2:
        return False
    yield DeflessHandled()
