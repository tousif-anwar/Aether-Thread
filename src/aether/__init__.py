"""
Aether-Thread: A concurrency-optimization toolkit for GIL-free Python.

Modern, developer-friendly tools for thread-safe Python code:
- @atomic decorator for automatic synchronization
- Thread-safe collections with smart locking
- Contention monitoring and diagnostics
- Performance benchmarking suite
"""

__version__ = "0.2.0"
__author__ = "Tousif Anwar"
__license__ = "MIT"

from .decorators import atomic, synchronized
from .collections import ThreadSafeList, ThreadSafeDict, ThreadSafeSet
from .monitor import ContentionMonitor, ContentionStats
from . import audit, benchmark

__all__ = [
    "atomic",
    "synchronized",
    "ThreadSafeList",
    "ThreadSafeDict",
    "ThreadSafeSet",
    "ContentionMonitor",
    "ContentionStats",
    "audit",
    "benchmark",
]
