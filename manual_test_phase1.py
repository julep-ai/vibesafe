import asyncio
from vibesafe import vibesafe, VibeCoded

@vibesafe
def hello(name: str) -> str:
    """
    >>> hello("World")
    'Hello, World!'
    """
    raise VibeCoded()

@vibesafe
async def async_hello(name: str) -> str:
    """
    >>> await async_hello("Async")
    'Hello, Async!'
    """
    raise VibeCoded()

def test_sync():
    print("Testing sync hello...")
    try:
        print(hello("World"))
    except Exception as e:
        print(f"Caught expected error (no API key/checkpoint): {e}")

async def test_async():
    print("Testing async hello...")
    try:
        print(await async_hello("Async"))
    except Exception as e:
        print(f"Caught expected error (no API key/checkpoint): {e}")

if __name__ == "__main__":
    test_sync()
    asyncio.run(test_async())
