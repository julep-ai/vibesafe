"""
Complex test cases for vibesafe to test markdown stripping.
"""

from vibesafe import VibeCoded, vibesafe


@vibesafe.func
def fibonacci_list(n: int) -> list[int]:
    """
    Generate list of first n Fibonacci numbers.

    >>> fibonacci_list(5)
    [0, 1, 1, 2, 3]
    >>> fibonacci_list(10)
    [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    >>> fibonacci_list(1)
    [0]
    >>> fibonacci_list(0)
    []
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    raise VibeCoded()


@vibesafe.func
def word_frequency(text: str) -> dict[str, int]:
    """
    Count word frequency in text (case-insensitive).

    >>> word_frequency("Hello world hello")
    {'hello': 2, 'world': 1}
    >>> word_frequency("The quick brown fox jumps over the lazy dog")
    {'the': 2, 'quick': 1, 'brown': 1, 'fox': 1, 'jumps': 1, 'over': 1, 'lazy': 1, 'dog': 1}
    >>> word_frequency("")
    {}
    """
    # Normalize text to lowercase for counting
    text = text.lower()
    raise VibeCoded()
