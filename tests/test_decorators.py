"""
Tests for decorators and thread-safe utilities.
"""

import pytest
import threading
import time
from aether_thread.decorators import (
    thread_safe, 
    gil_free_compatible,
    ThreadSafeCounter,
    ThreadSafeDict
)


def test_thread_safe_decorator():
    """Test the thread_safe decorator."""
    counter = 0
    
    @thread_safe
    def increment():
        nonlocal counter
        temp = counter
        time.sleep(0.001)  # Simulate work
        counter = temp + 1
    
    # Run in multiple threads
    threads = [threading.Thread(target=increment) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert counter == 10


def test_thread_safe_has_lock():
    """Test that thread_safe decorator adds a lock attribute."""
    @thread_safe
    def dummy():
        pass
    
    assert hasattr(dummy, '_lock')


def test_gil_free_compatible_decorator():
    """Test the gil_free_compatible decorator."""
    @gil_free_compatible(strict=False)
    def safe_func(x):
        return x * 2
    
    result = safe_func(5)
    assert result == 10
    assert hasattr(safe_func, '_gil_free_compatible')


def test_thread_safe_counter():
    """Test ThreadSafeCounter."""
    counter = ThreadSafeCounter(0)
    
    def worker():
        for _ in range(100):
            counter.increment()
    
    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert counter.value == 500


def test_thread_safe_counter_operations():
    """Test ThreadSafeCounter operations."""
    counter = ThreadSafeCounter(10)
    
    assert counter.value == 10
    assert counter.increment() == 11
    assert counter.increment(5) == 16
    assert counter.decrement() == 15
    assert counter.decrement(3) == 12
    
    counter.reset()
    assert counter.value == 0


def test_thread_safe_dict():
    """Test ThreadSafeDict."""
    d = ThreadSafeDict()
    
    d.set('key1', 'value1')
    assert d.get('key1') == 'value1'
    
    d.set('key2', 'value2')
    assert len(d.keys()) == 2
    
    d.delete('key1')
    assert d.get('key1') is None


def test_thread_safe_dict_concurrent():
    """Test ThreadSafeDict with concurrent access."""
    d = ThreadSafeDict()
    
    def writer(key, value):
        d.set(key, value)
    
    threads = [
        threading.Thread(target=writer, args=(f'key{i}', i))
        for i in range(20)
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(d.keys()) == 20


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
