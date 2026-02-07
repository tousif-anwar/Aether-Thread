"""
aether.audit: Static analysis for thread-safety issues.

Detects non-thread-safe patterns in Python code using AST analysis.
"""

from .analyzer import CodeAnalyzer
from .scanner import StaticScanner

__all__ = ["CodeAnalyzer", "StaticScanner"]
