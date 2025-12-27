"""Display utilities."""

import os
import platform


def clear_screen():
    """Clear the terminal screen."""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')


def print_header(title: str, width: int = 60):
    """Print a formatted header."""
    print("=" * width)
    print(f"     {title}")
    print("=" * width)
    print()


def print_section(title: str):
    """Print a section separator."""
    print()
    print(f"{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print()
