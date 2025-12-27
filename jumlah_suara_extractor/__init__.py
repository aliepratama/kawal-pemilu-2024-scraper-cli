"""Jumlah Suara Extractor - Auto-cropping for vote numbers using YOLOv11-seg."""

from .injector import Injector, create_injector
from .config import Settings

__version__ = '2.0.0'

__all__ = [
    'Injector',
    'create_injector',
    'Settings',
]
