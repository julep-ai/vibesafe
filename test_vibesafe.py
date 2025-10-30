"""
Test specs for demonstrating vibesafe functionality.
"""

from vibesafe import VibesafeHandled, vibesafe


@vibesafe.func
def multiply(a: int, b: int) -> int:
    """
    Multiply two integers.

    >>> multiply(2, 3)
    6
    >>> multiply(5, 7)
    35
    >>> multiply(-3, 4)
    -12
    >>> multiply(0, 10)
    0
    """
    yield VibesafeHandled()


@vibesafe.func
def factorial(n: int) -> int:
    """
    Calculate the factorial of a non-negative integer.

    >>> factorial(0)
    1
    >>> factorial(1)
    1
    >>> factorial(5)
    120
    >>> factorial(7)
    5040
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    yield VibesafeHandled()


@vibesafe.func
def reverse_string(text: str) -> str:
    """
    Reverse a string.

    >>> reverse_string("hello")
    'olleh'
    >>> reverse_string("Python")
    'nohtyP'
    >>> reverse_string("12345")
    '54321'
    >>> reverse_string("")
    ''
    """
    yield VibesafeHandled()
