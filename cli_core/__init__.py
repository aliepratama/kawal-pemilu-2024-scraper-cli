"""CLI Core - Modular CLI services with dependency injection."""

from .injector import CLIInjector, create_cli_injector
from .config import CLISettings

__version__ = '2.0.0'

__all__ = [
    'CLIInjector',
    'create_cli_injector',
    'CLISettings',
]
