"""
Thread-safe decorators for automatic synchronization.

Provides @atomic and @synchronized decorators that automatically handle
locking for methods and functions, with GIL-aware behavior.
"""

import functools
import sys
import threading
from typing import Any, Callable, Optional, TypeVar, overload, Union
from enum import Enum

F = TypeVar("F", bound=Callable[..., Any])


class LockType(Enum):
    """Types of locks that can be used for synchronization."""
    LOCK = "lock"
    RLOCK = "rlock"
    SEMAPHORE = "semaphore"


class SynchronizationStrategy(Enum):
    """Strategies for applying synchronization."""
    ALWAYS = "always"  # Always acquire lock
    GIL_DISABLED = "gil_disabled"  # Only when GIL is disabled
    ADAPTIVE = "adaptive"  # Adaptive based on contention


def _is_gil_enabled() -> bool:
    """Check if the Global Interpreter Lock is enabled."""
    if sys.version_info >= (3, 13):
        return sys._is_gil_enabled()
    return True  # GIL always enabled in Python < 3.13


def _create_lock(lock_type: LockType) -> Union[threading.Lock, threading.RLock, threading.Semaphore]:
    """Create a lock of the specified type."""
    if lock_type == LockType.LOCK:
        return threading.Lock()
    elif lock_type == LockType.RLOCK:
        return threading.RLock()
    elif lock_type == LockType.SEMAPHORE:
        return threading.Semaphore()
    else:
        return threading.RLock()


class AtomicDescriptor:
    """Descriptor that wraps instance methods with automatic synchronization."""
    
    def __init__(
        self,
        func: Callable,
        lock_type: LockType = LockType.RLOCK,
        strategy: SynchronizationStrategy = SynchronizationStrategy.ADAPTIVE,
        timeout: Optional[float] = None,
        track_contention: bool = False,
    ):
        self.func = func
        self.lock_type = lock_type
        self.strategy = strategy
        self.timeout = timeout
        self.track_contention = track_contention
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
        self.__wrapped__ = func
    
    def __set_name__(self, owner: type, name: str) -> None:
        """Called when descriptor is assigned to a class attribute."""
        self.name = name
    
    def __get__(self, instance: Any, owner: Optional[type] = None) -> Callable:
        """Return a bound method wrapper with synchronization."""
        if instance is None:
            return self
        
        # Get or create instance lock
        lock_attr = f"_atomic_lock_{self.name}"
        if not hasattr(instance, lock_attr):
            setattr(instance, lock_attr, _create_lock(self.lock_type))
        
        lock = getattr(instance, lock_attr)
        
        @functools.wraps(self.func)
        def synchronized_method(*args: Any, **kwargs: Any) -> Any:
            """Execute method with synchronization."""
            # Determine if we should acquire the lock
            should_lock = True
            if self.strategy == SynchronizationStrategy.GIL_DISABLED:
                should_lock = not _is_gil_enabled()
            elif self.strategy == SynchronizationStrategy.ADAPTIVE:
                # Always lock for safety, GIL will optimize if enabled
                should_lock = True
            
            if should_lock:
                if self.timeout is not None:
                    acquired = lock.acquire(timeout=self.timeout)
                else:
                    acquired = lock.acquire()
                    
                if not acquired and self.timeout is not None:
                    raise TimeoutError(
                        f"Could not acquire lock for {self.name} within {self.timeout} seconds"
                    )
                try:
                    return self.func(instance, *args, **kwargs)
                finally:
                    lock.release()
            else:
                return self.func(instance, *args, **kwargs)
        
        return synchronized_method


def atomic(
    func: Optional[F] = None,
    *,
    lock_type: LockType = LockType.RLOCK,
    strategy: SynchronizationStrategy = SynchronizationStrategy.ADAPTIVE,
    timeout: Optional[float] = None,
    track_contention: bool = False,
) -> Callable[[F], F] | Callable:
    """
    Decorator for atomic/thread-safe method execution.
    
    Automatically synchronizes method execution using a lock. The lock is
    stored as an instance attribute and can be controlled via parameters.
    
    Works with both instance methods and regular functions.
    
    Args:
        func: The function/method to decorate
        lock_type: Type of lock to use (LOCK, RLOCK, SEMAPHORE)
        strategy: When to acquire lock (ALWAYS, GIL_DISABLED, ADAPTIVE)
        timeout: Timeout for acquiring lock (None = infinite)
        track_contention: Whether to track contention metrics
        
    Returns:
        Decorated function with automatic synchronization
        
    Examples:
        With instance methods (descriptor-based):
        
        ```python
        class BankAccount:
            def __init__(self):
                self.balance = 0
            
            @atomic
            def deposit(self, amount):
                self.balance += amount
            
            @atomic
            def withdraw(self, amount):
                if self.balance >= amount:
                    self.balance -= amount
                    return amount
                return 0
        ```
        
        With custom lock type:
        
        ```python
        class Counter:
            def __init__(self):
                self.count = 0
            
            @atomic(lock_type=LockType.LOCK, timeout=5.0)
            def increment(self):
                self.count += 1
        ```
        
        With GIL-aware strategy:
        
        ```python
        @atomic(strategy=SynchronizationStrategy.GIL_DISABLED)
        def risky_operation():
            # Only locked when GIL is disabled (Python 3.13+)
            global_state.update()
        ```
    """
    def decorator(f: F) -> F:
        return AtomicDescriptor(
            f,
            lock_type=lock_type,
            strategy=strategy,
            timeout=timeout,
            track_contention=track_contention,
        )
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def synchronized(
    func: Optional[F] = None,
    *,
    timeout: Optional[float] = None,
) -> Callable[[F], F] | Callable:
    """
    Alias for @atomic with RLock by default.
    
    Provides the common use case of synchronizing a method without
    worrying about lock types or strategies.
    
    Args:
        func: The function/method to decorate
        timeout: Timeout for acquiring lock (None = infinite)
        
    Returns:
        Decorated function with automatic synchronization
        
    Examples:
        ```python
        class DataProcessor:
            def __init__(self):
                self.data = {}
            
            @synchronized
            def process(self, key, value):
                self.data[key] = transform(value)
        ```
    """
    def decorator(f: F) -> F:
        return AtomicDescriptor(
            f,
            lock_type=LockType.RLOCK,
            strategy=SynchronizationStrategy.ADAPTIVE,
            timeout=timeout,
            track_contention=False,
        )
    
    if func is None:
        return decorator
    else:
        return decorator(func)
