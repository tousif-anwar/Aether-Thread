"""
Tests for aether.decorators module.
"""

import unittest
import threading
import time
from aether.decorators import atomic, synchronized, LockType, SynchronizationStrategy


class TestAtomicDecorator(unittest.TestCase):
    """Test cases for @atomic decorator."""
    
    def test_basic_synchronization(self):
        """Test that @atomic prevents concurrent modifications."""
        class Counter:
            def __init__(self):
                self.value = 0
            
            @atomic
            def increment(self):
                # Simulate work
                temp = self.value
                time.sleep(0.001)
                self.value = temp + 1
        
        counter = Counter()
        threads = []
        
        # Increment from 10 threads
        for _ in range(10):
            t = threading.Thread(target=counter.increment)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # With @atomic, should be 10
        self.assertEqual(counter.value, 10)
    
    def test_multiple_methods(self):
        """Test multiple decorated methods on same object."""
        class BankAccount:
            def __init__(self):
                self.balance = 1000
            
            @atomic
            def deposit(self, amount):
                self.balance += amount
            
            @atomic
            def withdraw(self, amount):
                self.balance -= amount
            
            @atomic
            def get_balance(self):
                return self.balance
        
        account = BankAccount()
        
        def worker():
            account.deposit(10)
            account.withdraw(5)
            account.deposit(20)
        
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Each worker adds net 25, so 1000 + (5 * 25) = 1125
        self.assertEqual(account.get_balance(), 1125)
    
    def test_with_return_values(self):
        """Test that decorated methods return values correctly."""
        class Accumulator:
            def __init__(self):
                self.total = 0
            
            @atomic
            def add_and_return(self, value):
                self.total += value
                return self.total
        
        acc = Accumulator()
        result1 = acc.add_and_return(5)
        result2 = acc.add_and_return(3)
        
        self.assertEqual(result1, 5)
        self.assertEqual(result2, 8)
    
    def test_synchronized_alias(self):
        """Test that @synchronized is an alias for @atomic."""
        class SafeCounter:
            def __init__(self):
                self.count = 0
            
            @synchronized
            def increment(self):
                self.count += 1
        
        counter = SafeCounter()
        threads = [threading.Thread(target=counter.increment) for _ in range(100)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(counter.count, 100)
    
    def test_with_exceptions(self):
        """Test that locks are released even when exceptions occur."""
        class Risky:
            def __init__(self):
                self.value = 0
                self.calls = 0
            
            @atomic
            def risky_operation(self, should_fail):
                self.calls += 1
                if should_fail:
                    raise ValueError("Intentional error")
                self.value += 1
        
        risky = Risky()
        
        try:
            risky.risky_operation(True)
        except ValueError:
            pass
        
        # Lock should still work after exception
        risky.risky_operation(False)
        self.assertEqual(risky.value, 1)
        self.assertEqual(risky.calls, 2)
    
    def test_reentrant_locking(self):
        """Test that RLock allows reentrant calls."""
        class ReentrantClass:
            def __init__(self):
                self.value = 0
            
            @atomic(lock_type=LockType.RLOCK)
            def outer(self):
                self.value += 1
                self.inner()
            
            @atomic(lock_type=LockType.RLOCK)
            def inner(self):
                self.value += 10
        
        obj = ReentrantClass()
        obj.outer()
        
        # Should not deadlock
        self.assertEqual(obj.value, 11)
    
    def test_custom_lock_type(self):
        """Test using different lock types."""
        class WithLock:
            def __init__(self):
                self.count = 0
            
            @atomic(lock_type=LockType.LOCK)
            def increment(self):
                self.count += 1
        
        obj = WithLock()
        threads = [threading.Thread(target=obj.increment) for _ in range(50)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(obj.count, 50)


class TestSynchronizedDecorator(unittest.TestCase):
    """Test cases for @synchronized decorator."""
    
    def test_basic_functionality(self):
        """Test basic @synchronized usage."""
        class Queue:
            def __init__(self):
                self.items = []
            
            @synchronized
            def enqueue(self, item):
                self.items.append(item)
            
            @synchronized
            def dequeue(self):
                if self.items:
                    return self.items.pop(0)
                return None
        
        queue = Queue()
        queue.enqueue(1)
        queue.enqueue(2)
        
        self.assertEqual(queue.dequeue(), 1)
        self.assertEqual(queue.dequeue(), 2)
    
    def test_concurrent_queue_operations(self):
        """Test thread-safe queue operations."""
        class ThreadSafeQueue:
            def __init__(self):
                self.items = []
            
            @synchronized
            def enqueue(self, item):
                self.items.append(item)
            
            @synchronized
            def size(self):
                return len(self.items)
        
        queue = ThreadSafeQueue()
        
        def producer():
            for i in range(100):
                queue.enqueue(i)
        
        threads = [threading.Thread(target=producer) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(queue.size(), 500)


if __name__ == '__main__':
    unittest.main()
