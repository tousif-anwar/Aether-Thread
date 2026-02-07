"""
Thread-safe wrappers for Python standard collections.
"""

from typing import Any, List, Dict, Optional, Iterator, Tuple
from .wrapper import ThreadSafeWrapper


class ThreadSafeList(ThreadSafeWrapper):
    """
    Thread-safe wrapper for Python list.
    
    Provides fine-grained locking when GIL is disabled.
    """
    
    def __init__(self, obj: Optional[List] = None):
        """Initialize with optional initial list."""
        if obj is None:
            obj = []
        elif not isinstance(obj, list):
            obj = list(obj)
        super().__init__(obj)
    
    def append(self, item: Any) -> None:
        """Append an item to the list."""
        self._with_lock(lambda: self._object.append(item))
    
    def extend(self, items: List) -> None:
        """Extend the list with multiple items."""
        self._with_lock(lambda: self._object.extend(items))
    
    def insert(self, index: int, item: Any) -> None:
        """Insert an item at a specific index."""
        self._with_lock(lambda: self._object.insert(index, item))
    
    def remove(self, item: Any) -> None:
        """Remove the first occurrence of an item."""
        self._with_lock(lambda: self._object.remove(item))
    
    def pop(self, index: int = -1) -> Any:
        """Remove and return item at index."""
        return self._with_lock(lambda: self._object.pop(index))
    
    def clear(self) -> None:
        """Remove all items."""
        self._with_lock(lambda: self._object.clear())
    
    def __getitem__(self, index: int) -> Any:
        """Get item at index."""
        return self._with_lock(lambda: self._object[index])
    
    def __setitem__(self, index: int, value: Any) -> None:
        """Set item at index."""
        self._with_lock(lambda: self._object.__setitem__(index, value))
    
    def __len__(self) -> int:
        """Get list length."""
        return self._with_lock(lambda: len(self._object))
    
    def __iter__(self) -> Iterator:
        """Iterate over items (snapshot to avoid concurrent modification issues)."""
        # Create a snapshot to safely iterate
        return iter(self._with_lock(lambda: self._object.copy()))
    
    def __contains__(self, item: Any) -> bool:
        """Check if item is in list."""
        return self._with_lock(lambda: item in self._object)


class ThreadSafeDict(ThreadSafeWrapper):
    """
    Thread-safe wrapper for Python dict.
    
    Provides fine-grained locking when GIL is disabled.
    """
    
    def __init__(self, obj: Optional[Dict] = None):
        """Initialize with optional initial dict."""
        if obj is None:
            obj = {}
        elif not isinstance(obj, dict):
            obj = dict(obj)
        super().__init__(obj)
    
    def __setitem__(self, key: Any, value: Any) -> None:
        """Set a key-value pair."""
        self._with_lock(lambda: self._object.__setitem__(key, value))
    
    def __getitem__(self, key: Any) -> Any:
        """Get value for a key."""
        return self._with_lock(lambda: self._object[key])
    
    def __delitem__(self, key: Any) -> None:
        """Delete a key."""
        self._with_lock(lambda: self._object.__delitem__(key))
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Get value for a key with default."""
        return self._with_lock(lambda: self._object.get(key, default))
    
    def pop(self, key: Any, *args) -> Any:
        """Remove and return value for a key."""
        return self._with_lock(lambda: self._object.pop(key, *args))
    
    def update(self, other: Dict) -> None:
        """Update with another dict."""
        self._with_lock(lambda: self._object.update(other))
    
    def clear(self) -> None:
        """Remove all items."""
        self._with_lock(lambda: self._object.clear())
    
    def __len__(self) -> int:
        """Get dict size."""
        return self._with_lock(lambda: len(self._object))
    
    def __contains__(self, key: Any) -> bool:
        """Check if key is in dict."""
        return self._with_lock(lambda: key in self._object)
    
    def __iter__(self) -> Iterator:
        """Iterate over keys (snapshot to avoid concurrent modification issues)."""
        return iter(self._with_lock(lambda: list(self._object.keys())))
    
    def keys(self):
        """Get dictionary keys (snapshot)."""
        return self._with_lock(lambda: list(self._object.keys()))
    
    def values(self):
        """Get dictionary values (snapshot)."""
        return self._with_lock(lambda: list(self._object.values()))
    
    def items(self):
        """Get dictionary items (snapshot)."""
        return self._with_lock(lambda: list(self._object.items()))
