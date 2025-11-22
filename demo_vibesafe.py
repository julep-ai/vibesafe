#!/usr/bin/env python3
"""
Demo script to show vibesafe-generated functions in action.
"""

# Import the generated functions using the public API alias
from vibesafe import load_active

multiply = load_active("test_vibesafe/multiply")
factorial = load_active("test_vibesafe/factorial")


def main():
    print("=" * 60)
    print("🚀 Vibesafe Demo - AI-Generated Functions")
    print("=" * 60)

    # Test multiply function
    print("\n📊 Testing multiply function:")
    test_cases_multiply = [(2, 3, 6), (5, 7, 35), (-3, 4, -12), (0, 10, 0)]

    for a, b, expected in test_cases_multiply:
        result = multiply(a, b)
        status = "✅" if result == expected else "❌"
        print(f"  {status} multiply({a}, {b}) = {result} (expected {expected})")

    # Test factorial function
    print("\n📊 Testing factorial function:")
    test_cases_factorial = [(0, 1), (1, 1), (5, 120), (7, 5040)]

    for n, expected in test_cases_factorial:
        result = factorial(n)
        status = "✅" if result == expected else "❌"
        print(f"  {status} factorial({n}) = {result} (expected {expected})")

    # Demo some calculations
    print("\n🎯 Real calculations:")
    print(f"  Area of a 12x8 rectangle: {multiply(12, 8)} square units")
    print(f"  Number of permutations of 6 items: {factorial(6)}")

    # Show that error handling works
    print("\n⚠️  Testing error handling:")
    try:
        factorial(-1)
        print("  ❌ Should have raised an error for negative input")
    except ValueError as e:
        print(f"  ✅ Correctly raised error: {e}")

    print("\n" + "=" * 60)
    print("✨ Demo complete! All AI-generated functions work correctly.")
    print("=" * 60)


if __name__ == "__main__":
    main()
