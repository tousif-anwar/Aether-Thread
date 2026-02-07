"""
Aether-Thread: A concurrency-optimization toolkit for GIL-free Python.

Modern, developer-friendly tools for thread-safe Python code:
- @atomic decorator for automatic synchronization
- Thread-safe collections with smart locking
- Contention monitoring and diagnostics
- Performance benchmarking suite
- Free-threaded Python (3.13+) support
- Saturation cliff detection and profiling
- Adaptive thread pool with contention awareness
- GIL status checker and environment validation
"""

__version__ = "0.3.0"
__author__ = "Tousif Anwar"
__license__ = "MIT"

from .decorators import atomic, synchronized
from .collections import ThreadSafeList, ThreadSafeDict, ThreadSafeSet
from .monitor import ContentionMonitor, ContentionStats
from . import audit, benchmark

# New in v0.3.0: Free-threading support
try:
    from .check import GILStatusChecker, get_gil_status, is_free_threaded
    from .pool import AdaptiveThreadPool, adaptive_pool
    from .profile import SaturationCliffProfiler, benchmark_function
    from . import cli
except ImportError:
    # Optional imports for environments without psutil
    pass

__all__ = [
    # Core v0.1.0-0.2.0
    "atomic",
    "synchronized",
    "ThreadSafeList",
    "ThreadSafeDict",
    "ThreadSafeSet",
    "ContentionMonitor",
    "ContentionStats",
    "audit",
    "benchmark",
    # New v0.3.0
    "GILStatusChecker",
    "get_gil_status",
    "is_free_threaded",
    "AdaptiveThreadPool",
    "adaptive_pool",
    "SaturationCliffProfiler",
    "benchmark_function",
    "cli",
]
