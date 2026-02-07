"""
aether-bench: Benchmarking suite for concurrent performance.

Compares performance across:
- Different Python versions
- GIL-on vs GIL-off configurations
- Lock-free vs locking implementations
"""

from .benchmarker import Benchmarker
from .runner import BenchmarkRunner

__all__ = ["Benchmarker", "BenchmarkRunner"]
