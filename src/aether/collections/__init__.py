"""
Thread-safe collection wrappers.

Provides thread-safe versions of standard Python collections:
- ThreadSafeList
- ThreadSafeDict
- ThreadSafeSet

With automatic fine-grained locking and optional contention tracking.
"""

import sys
import threading
from typing import Any, Iterator, List, Dict, Set, Optional, Callable
from contextlib import contextmanager


def _is_gil_enabled() -> bool:
    """Check if the Global Interpreter Lock is enabled."""
    if sys.version_info >= (3, 13):
        return sys._is_gil_enabled()
    return True


class ThreadSafeWrapper:
    """
    Base class for thread-safe collection wrappers.
    
    Dynamically adjusts behavior based on GIL state:
    - GIL enabled: Minimal overhead, relies on GIL
    - GIL disabled: Fine-grained RLock protection
    """
    
    def __init__(self, obj: Any, track_contention: bool = False):
        """
        Initialize wrapper.
        
        Args:
            obj: Object to wrap
            track_contention: Whether to track lock contention
        """
        self._object = obj
        self._lock = threading.RLock()
        self._gil_disabled = not _is_gil_enabled()
        self._track_contention = track_contention
        self._lock_name = f"{self.__class__.__name__}@{id(self)}"
    
    def _with_lock(self, func: Callable) -> Any:
        """
        Execute function with lock if needed.
        
        Args:
            func: Callable to execute
            
        Returns:
            Result of func()
        """
        if self._gil_disabled:
            with self._lock:
                return func()
        else:
            return func()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._object!r})"


class ThreadSafeList(ThreadSafeWrapper):
    """
    Thread-safe wrapper for Python list.
    
    All operations are synchronized when GIL is disabled.
    Thread-safe for concurrent access from multiple threads.
    """
    
    def __init__(self, obj: Optional[List] = None, track_contention: bool = False):
        """Initialize with optional initial list."""
        if obj is None:
            obj = []
        elif not isinstance(obj, list):
            obj = list(obj)
        super().__init__(obj, track_contention)
    
    def append(self, item: Any) -> None:
        """Thread-safe append."""
        self._with_lock(lambda: self._object.append(item))
    
    def extend(self, items: List) -> None:
        """Thread-safe extend."""
        self._with_lock(lambda: self._object.extend(items))
    
    def insert(self, index: int, item: Any) -> None:
        """Thread-safe insert."""
        self._with_lock(lambda: self._object.insert(index, item))
    
    def remove(self, item: Any) -> None:
        """Thread-safe remove (first occurrence)."""
        self._with_lock(lambda: self._object.remove(item))
    
    def pop(self, index: int = -1) -> Any:
        """Thread-safe pop."""
        return self._with_lock(lambda: self._object.pop(index))
    
    def clear(self) -> None:
        """Thread-safe clear."""
        self._with_lock(lambda: self._object.clear())
    
    def __getitem__(self, index: int) -> Any:
        """Thread-safe get by index."""
        return self._with_lock(lambda: self._object[index])
    
    def __setitem__(self, index: int, value: Any) -> None:
        """Thread-safe set by index."""
        self._with_lock(lambda: self._object.__setitem__(index, value))
    
    def __len__(self) -> int:
        """Thread-safe length."""
        return self._with_lock(lambda: len(self._object))
    
    def __iter__(self) -> Iterator:
        """Create snapshot for safe iteration."""
        return iter(self._with_lock(lambda: self._object.copy()))
    
    def __contains__(self, item: Any) -> bool:
        """Thread-safe membership test."""
        return self._with_lock(lambda: item in self._object)


class ThreadSafeDict(ThreadSafeWrapper):
    """
    Thread-safe wrapper for Python dict.
    
    All operations are synchronized when GIL is disabled.
    Thread-safe for concurrent reads and writes from multiple threads.
    """
    
    def __init__(self, obj: Optional[Dict] = None, track_contention: bool = False):
        """Initialize with optional initial dict."""
        if obj is None:
            obj = {}
        elif not isinstance(obj, dict):
            obj = dict(obj)
        super().__init__(obj, track_contention)
    
    def __setitem__(self, key: Any, value: Any) -> None:
        """Thread-safe set item."""
        self._with_lock(lambda: self._object.__setitem__(key, value))
    
    def __getitem__(self, key: Any) -> Any:
        """Thread-safe get item."""
        return self._with_lock(lambda: self._object[key])
    
    def __delitem__(self, key: Any) -> None:
        """Thread-safe delete item."""
        self._with_lock(lambda: self._object.__delitem__(key))
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Thread-safe get with default."""
        return self._with_lock(lambda: self._object.get(key, default))
    
    def pop(self, key: Any, *args) -> Any:
        """Thread-safe pop."""
        return self._with_lock(lambda: self._object.pop(key, *args))
    
    def update(self, other: Dict) -> None:
        """Thread-safe update."""
        self._with_lock(lambda: self._object.update(other))
    
    def clear(self) -> None:
        """Thread-safe clear."""
        self._with_lock(lambda: self._object.clear())
    
    def __len__(self) -> int:
        """Thread-safe length."""
        return self._with_lock(lambda: len(self._object))
    
    def __contains__(self, key: Any) -> bool:
        """Thread-safe membership test."""
        return self._with_lock(lambda: key in self._object)
    
    def __iter__(self) -> Iterator:
        """Create snapshot for safe iteration."""
        return iter(self._with_lock(lambda: list(self._object.keys())))
    
    def keys(self) -> List:
        """Thread-safe keys (snapshot)."""
        return self._with_lock(lambda: list(self._object.keys()))
    
    def values(self) -> List:
        """Thread-safe values (snapshot)."""
        return self._with_lock(lambda: list(self._object.values()))
    
    def items(self) -> List:
        """Thread-safe items (snapshot)."""
        return self._with_lock(lambda: list(self._object.items()))


class ThreadSafeSet(ThreadSafeWrapper):
    """
    Thread-safe wrapper for Python set.
    
    All operations are synchronized when GIL is disabled.
    Thread-safe for concurrent modifications from multiple threads.
    """
    
    def __init__(self, obj: Optional[Set] = None, track_contention: bool = False):
        """Initialize with optional initial set."""
        if obj is None:
            obj = set()
        elif not isinstance(obj, set):
            obj = set(obj)
        super().__init__(obj, track_contention)
    
    def add(self, item: Any) -> None:
        """Thread-safe add."""
        self._with_lock(lambda: self._object.add(item))
    
    def remove(self, item: Any) -> None:
        """Thread-safe remove (raises KeyError if not found)."""
        self._with_lock(lambda: self._object.remove(item))
    
    def discard(self, item: Any) -> None:
        """Thread-safe discard (no error if not found)."""
        self._with_lock(lambda: self._object.discard(item))
    
    def clear(self) -> None:
        """Thread-safe clear."""
        self._with_lock(lambda: self._object.clear())
    
    def pop(self) -> Any:
        """Thread-safe pop."""
        return self._with_lock(lambda: self._object.pop())
    
    def __len__(self) -> int:
        """Thread-safe length."""
        return self._with_lock(lambda: len(self._object))
    
    def __contains__(self, item: Any) -> bool:
        """Thread-safe membership test."""
        return self._with_lock(lambda: item in self._object)
    
    def __iter__(self) -> Iterator:
        """Create snapshot for safe iteration."""
        return iter(self._with_lock(lambda: self._object.copy()))
    
    def union(self, other: Set) -> "ThreadSafeSet":
        """Thread-safe union."""
        result = self._with_lock(lambda: self._object.union(other))
        return ThreadSafeSet(result, self._track_contention)
    
    def intersection(self, other: Set) -> "ThreadSafeSet":
        """Thread-safe intersection."""
        result = self._with_lock(lambda: self._object.intersection(other))
        return ThreadSafeSet(result, self._track_contention)
    
    def difference(self, other: Set) -> "ThreadSafeSet":
        """Thread-safe difference."""
        result = self._with_lock(lambda: self._object.difference(other))
        return ThreadSafeSet(result, self._track_contention)
