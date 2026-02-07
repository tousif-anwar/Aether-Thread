"""
Aether-Thread: A concurrency-optimization toolkit for GIL-free Python.

This toolkit helps Python developers transition their legacy code to thread-safe,
GIL-free environments by providing analysis, transformation, and profiling tools.
"""

__version__ = "0.1.0"
__author__ = "Tousif Anwar"

from aether_thread.analyzer import ThreadSafetyAnalyzer
from aether_thread.decorators import (
    thread_safe, 
    gil_free_compatible,
    ThreadSafeCounter,
    ThreadSafeDict
)
from aether_thread.profiler import GILContentionProfiler
from aether_thread.transformer import CodeTransformer

__all__ = [
    "ThreadSafetyAnalyzer",
    "thread_safe",
    "gil_free_compatible",
    "ThreadSafeCounter",
    "ThreadSafeDict",
    "GILContentionProfiler",
    "CodeTransformer",
]
