"""
Tests for aether-proxy module.
"""

import unittest
import threading
from aether_thread.proxy import ThreadSafeList, ThreadSafeDict


class TestThreadSafeList(unittest.TestCase):
    """Test cases for ThreadSafeList."""
    
    def test_basic_operations(self):
        """Test basic list operations."""
        lst = ThreadSafeList()
        
        lst.append(1)
        lst.append(2)
        lst.extend([3, 4])
        
        self.assertEqual(len(lst), 4)
        self.assertEqual(lst[0], 1)
        self.assertEqual(lst[-1], 4)
    
    def test_concurrent_append(self):
        """Test concurrent append operations."""
        lst = ThreadSafeList()
        num_threads = 4
        items_per_thread = 100
        
        def append_items(start, end):
            for i in range(start, end):
                lst.append(i)
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(
                target=append_items,
                args=(i * items_per_thread, (i + 1) * items_per_thread)
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All items should be present
        self.assertEqual(len(lst), num_threads * items_per_thread)
    
    def test_remove_operation(self):
        """Test remove operation."""
        lst = ThreadSafeList([1, 2, 3, 2, 4])
        lst.remove(2)
        self.assertEqual(len(lst), 4)
    
    def test_pop_operation(self):
        """Test pop operation."""
        lst = ThreadSafeList([1, 2, 3])
        item = lst.pop()
        self.assertEqual(item, 3)
        self.assertEqual(len(lst), 2)
    
    def test_contains_operation(self):
        """Test contains check."""
        lst = ThreadSafeList([1, 2, 3])
        self.assertTrue(2 in lst)
        self.assertFalse(5 in lst)


class TestThreadSafeDict(unittest.TestCase):
    """Test cases for ThreadSafeDict."""
    
    def test_basic_operations(self):
        """Test basic dict operations."""
        d = ThreadSafeDict()
        
        d['key1'] = 'value1'
        d['key2'] = 'value2'
        
        self.assertEqual(len(d), 2)
        self.assertEqual(d['key1'], 'value1')
    
    def test_get_with_default(self):
        """Test get with default value."""
        d = ThreadSafeDict({'a': 1})
        
        self.assertEqual(d.get('a'), 1)
        self.assertEqual(d.get('b'), None)
        self.assertEqual(d.get('b', 'default'), 'default')
    
    def test_concurrent_updates(self):
        """Test concurrent dict updates."""
        d = ThreadSafeDict()
        num_threads = 4
        items_per_thread = 100
        
        def update_dict(thread_id):
            for i in range(items_per_thread):
                key = f"t{thread_id}_k{i}"
                d[key] = thread_id * 1000 + i
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=update_dict, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All items should be present
        self.assertEqual(len(d), num_threads * items_per_thread)
    
    def test_pop_operation(self):
        """Test pop operation."""
        d = ThreadSafeDict({'a': 1, 'b': 2})
        value = d.pop('a')
        
        self.assertEqual(value, 1)
        self.assertEqual(len(d), 1)
    
    def test_contains_operation(self):
        """Test contains check."""
        d = ThreadSafeDict({'a': 1, 'b': 2})
        self.assertTrue('a' in d)
        self.assertFalse('c' in d)


if __name__ == '__main__':
    unittest.main()
