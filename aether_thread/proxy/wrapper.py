"""
Base wrapper for thread-safe collections.
"""

import sys
import threading
from typing import Any, Callable, Optional


class ThreadSafeWrapper:
    """
    Base class for thread-safe wrappers that automatically manage locking.
    
    Dynamically adjusts behavior based on GIL state:
    - When GIL is enabled: Minimal overhead, relies on GIL for atomicity
    - When GIL is disabled: Uses fine-grained locking for safety
    """
    
    def __init__(self, obj: Any):
        """
        Initialize wrapper.
        
        Args:
            obj: The object to wrap
        """
        self._object = obj
        self._lock = threading.RLock()  # Reentrant lock for nested operations
        self._gil_disabled = self._is_gil_disabled()
        
    @staticmethod
    def _is_gil_disabled() -> bool:
        """Check if the GIL is disabled."""
        if sys.version_info >= (3, 13):
            return not sys._is_gil_enabled()
        return False
    
    def _with_lock(self, func: Callable) -> Any:
        """
        Execute a function with lock if GIL is disabled.
        
        Args:
            func: Callable that modifies the underlying object
            
        Returns:
            Result of the function call
        """
        if self._gil_disabled:
            with self._lock:
                return func()
        else:
            return func()
    
    def _with_lock_and_return(self, func: Callable) -> Any:
        """Execute function and return result, with lock if needed."""
        return self._with_lock(func)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._object!r})"
