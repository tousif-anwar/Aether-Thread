"""
aether-proxy: Smart thread-safe wrappers for Python collections.

Provides automatic fine-grained locking:
- ThreadSafeList: Wraps list with mutex management
- ThreadSafeDict: Wraps dict with mutex management
- Dynamic behavior based on GIL state
"""

from .collections import ThreadSafeList, ThreadSafeDict
from .wrapper import ThreadSafeWrapper

__all__ = ["ThreadSafeList", "ThreadSafeDict", "ThreadSafeWrapper"]
