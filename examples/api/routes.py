"""
Example vibesafe HTTP endpoints.
"""

from vibesafe import VibesafeHandled, vibesafe


@vibesafe(kind="http", method="POST", path="/sum")
async def sum_endpoint(a: int, b: int) -> dict[str, int]:
    """
    Add two numbers and return the result.

    Returns a dictionary with the sum.

    >>> import anyio
    >>> anyio.run(sum_endpoint, 2, 3)
    {'sum': 5}
    >>> anyio.run(sum_endpoint, 10, 20)
    {'sum': 30}
    """
    return VibesafeHandled()


@vibesafe(kind="http", method="GET", path="/hello/{name}")
async def hello_endpoint(name: str) -> dict[str, str]:
    """
    Greet a user by name.

    >>> import anyio
    >>> anyio.run(hello_endpoint, "Alice")
    {'message': 'Hello, Alice!'}
    >>> anyio.run(hello_endpoint, "Bob")
    {'message': 'Hello, Bob!'}
    """
    return VibesafeHandled()
