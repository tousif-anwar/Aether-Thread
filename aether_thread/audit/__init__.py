"""
aether-audit: Static analysis tool for detecting non-thread-safe patterns.

Scans a codebase and flags:
- Global variables
- Shared class attributes
- Mutable state without locks
"""

from .analyzer import CodeAnalyzer
from .scanner import StaticScanner

__all__ = ["CodeAnalyzer", "StaticScanner"]
