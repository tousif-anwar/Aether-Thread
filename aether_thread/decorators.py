"""
Decorators for thread-safe code development.
"""

import functools
import threading
import warnings
from typing import Any, Callable, TypeVar, cast


F = TypeVar('F', bound=Callable[..., Any])


def thread_safe(func: F) -> F:
    """
    Decorator to make a function thread-safe using a lock.
    
    This decorator wraps a function with a lock to ensure that only one thread
    can execute it at a time. This is useful for protecting shared state.
    
    Example:
        @thread_safe
        def increment_counter():
            global counter
            counter += 1
    
    Args:
        func: The function to make thread-safe
        
    Returns:
        A thread-safe version of the function
    """
    lock = threading.RLock()
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with lock:
            return func(*args, **kwargs)
    
    # Store lock as attribute for testing/inspection
    wrapper._lock = lock  # type: ignore
    return cast(F, wrapper)


def gil_free_compatible(strict: bool = False) -> Callable[[F], F]:
    """
    Decorator to mark and verify that a function is compatible with GIL-free mode.
    
    This decorator performs runtime checks to ensure the function doesn't use
    patterns that rely on the GIL for thread safety.
    
    Args:
        strict: If True, raises exceptions on compatibility issues.
                If False, only issues warnings.
    
    Example:
        @gil_free_compatible(strict=True)
        def safe_computation(data):
            # This function should not rely on GIL protection
            return sum(data)
    
    Returns:
        A decorator function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check for global variable access (basic check)
            if hasattr(func, '__globals__'):
                global_writes = []
                # This is a simplified check - a full implementation would
                # use AST analysis
                func_globals = func.__globals__
                if any(k.startswith('_unsafe_') for k in func_globals.keys()):
                    msg = f"Function {func.__name__} may access unsafe globals"
                    if strict:
                        raise RuntimeError(msg)
                    else:
                        warnings.warn(msg, RuntimeWarning)
            
            return func(*args, **kwargs)
        
        # Mark the function as GIL-free compatible
        wrapper._gil_free_compatible = True  # type: ignore
        wrapper._strict_mode = strict  # type: ignore
        return cast(F, wrapper)
    
    return decorator


class ThreadSafeCounter:
    """
    A thread-safe counter implementation.
    
    Example usage demonstrating proper thread-safe patterns.
    """
    
    def __init__(self, initial: int = 0) -> None:
        self._value = initial
        self._lock = threading.Lock()
    
    def increment(self, delta: int = 1) -> int:
        """Increment the counter atomically."""
        with self._lock:
            self._value += delta
            return self._value
    
    def decrement(self, delta: int = 1) -> int:
        """Decrement the counter atomically."""
        with self._lock:
            self._value -= delta
            return self._value
    
    @property
    def value(self) -> int:
        """Get the current value."""
        with self._lock:
            return self._value
    
    def reset(self) -> None:
        """Reset the counter to zero."""
        with self._lock:
            self._value = 0


class ThreadSafeDict:
    """
    A thread-safe dictionary wrapper.
    
    Provides synchronized access to a dictionary.
    """
    
    def __init__(self) -> None:
        self._dict: dict = {}
        self._lock = threading.RLock()
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Get a value from the dictionary."""
        with self._lock:
            return self._dict.get(key, default)
    
    def set(self, key: Any, value: Any) -> None:
        """Set a value in the dictionary."""
        with self._lock:
            self._dict[key] = value
    
    def delete(self, key: Any) -> None:
        """Delete a key from the dictionary."""
        with self._lock:
            if key in self._dict:
                del self._dict[key]
    
    def keys(self) -> list:
        """Get all keys (returns a copy)."""
        with self._lock:
            return list(self._dict.keys())
    
    def values(self) -> list:
        """Get all values (returns a copy)."""
        with self._lock:
            return list(self._dict.values())
    
    def items(self) -> list:
        """Get all items (returns a copy)."""
        with self._lock:
            return list(self._dict.items())
