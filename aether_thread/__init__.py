"""
Aether-Thread: A concurrency-optimization toolkit for Python.

Helps Python developers transition legacy code to a thread-safe, GIL-free environment.
"""

__version__ = "0.1.0"
__author__ = "Tousif Anwar"
__license__ = "MIT"

from . import audit, proxy, bench

__all__ = ["audit", "proxy", "bench"]
