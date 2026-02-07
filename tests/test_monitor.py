"""
Tests for aether.monitor module.
"""

import unittest
import threading
import time
from aether.monitor import ContentionMonitor, ContentionMetrics, ContentionLevel, get_monitor


class TestContentionMonitor(unittest.TestCase):
    """Test cases for ContentionMonitor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = get_monitor()
        self.monitor.clear()
    
    def test_singleton_instance(self):
        """Test that ContentionMonitor is a singleton."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        self.assertIs(monitor1, monitor2)
    
    def test_enable_disable(self):
        """Test enabling and disabling monitoring."""
        self.monitor.disable()
        self.assertFalse(self.monitor._enabled)
        
        self.monitor.enable()
        self.assertTrue(self.monitor._enabled)
    
    def test_track_acquisition(self):
        """Test tracking lock acquisitions."""
        self.monitor.enable()
        
        self.monitor.track_acquisition("test_lock", acquired=True, wait_time=0.001)
        self.monitor.track_acquisition("test_lock", acquired=True, wait_time=0.002)
        
        stats = self.monitor.get_stats()
        self.assertIn("test_lock", stats.metrics)
        self.assertEqual(stats.metrics["test_lock"].total_acquisitions, 2)
    
    def test_contention_tracking(self):
        """Test tracking contention."""
        self.monitor.enable()
        
        # Simulate 10 acquisitions with 3 having contention
        for i in range(10):
            self.monitor.track_acquisition("contested_lock", acquired=True, wait_time=0.001)
            if i < 3:
                self.monitor.track_contention("contested_lock")
        
        stats = self.monitor.get_stats()
        metrics = stats.metrics["contested_lock"]
        
        self.assertEqual(metrics.contention_count, 3)
        self.assertEqual(metrics.total_acquisitions, 10)
        self.assertAlmostEqual(metrics.contention_rate, 30.0, places=1)
    
    def test_contention_levels(self):
        """Test contention level classification."""
        # No contention
        metrics = ContentionMetrics("none_lock")
        metrics.total_acquisitions = 10
        metrics.contention_count = 0
        self.assertEqual(metrics.contention_level, ContentionLevel.NONE)
        
        # Low contention (< 10%)
        metrics = ContentionMetrics("low_lock")
        metrics.total_acquisitions = 100
        metrics.contention_count = 5
        self.assertEqual(metrics.contention_level, ContentionLevel.LOW)
        
        # High contention (> 50%)
        metrics = ContentionMetrics("high_lock")
        metrics.total_acquisitions = 100
        metrics.contention_count = 75
        self.assertEqual(metrics.contention_level, ContentionLevel.CRITICAL)
    
    def test_get_hot_locks(self):
        """Test identifying hot locks."""
        self.monitor.enable()
        
        # Hot lock with 30% contention
        for i in range(100):
            self.monitor.track_acquisition("hot_lock", acquired=True, wait_time=0.001)
            if i < 30:
                self.monitor.track_contention("hot_lock")
        
        # Cool lock with 5% contention
        for i in range(100):
            self.monitor.track_acquisition("cool_lock", acquired=True, wait_time=0.001)
            if i < 5:
                self.monitor.track_contention("cool_lock")
        
        stats = self.monitor.get_stats()
        hot_locks = stats.get_hot_locks(threshold=20.0)
        
        # Should only include hot_lock
        hot_names = [name for name, _ in hot_locks]
        self.assertIn("hot_lock", hot_names)
        self.assertNotIn("cool_lock", hot_names)
    
    def test_clear(self):
        """Test clearing metrics."""
        self.monitor.enable()
        self.monitor.track_acquisition("test_lock", acquired=True, wait_time=0.001)
        
        stats = self.monitor.get_stats()
        self.assertEqual(len(stats.metrics), 1)
        
        self.monitor.clear()
        stats = self.monitor.get_stats()
        self.assertEqual(len(stats.metrics), 0)


class TestContentionMetrics(unittest.TestCase):
    """Test cases for ContentionMetrics."""
    
    def test_average_times(self):
        """Test average time calculations."""
        metrics = ContentionMetrics("test_lock")
        metrics.total_acquisitions = 10
        metrics.total_wait_time = 0.1  # 100ms total
        metrics.total_hold_time = 0.5  # 500ms total
        
        self.assertAlmostEqual(metrics.average_wait_time, 0.01, places=3)
        self.assertAlmostEqual(metrics.average_hold_time, 0.05, places=3)
    
    def test_contention_rate(self):
        """Test contention rate calculation."""
        metrics = ContentionMetrics("test_lock")
        metrics.total_acquisitions = 100
        metrics.contention_count = 25
        
        self.assertAlmostEqual(metrics.contention_rate, 25.0, places=1)
    
    def test_zero_acquisitions(self):
        """Test metrics with zero acquisitions."""
        metrics = ContentionMetrics("empty_lock")
        
        self.assertEqual(metrics.average_wait_time, 0.0)
        self.assertEqual(metrics.average_hold_time, 0.0)
        self.assertEqual(metrics.contention_rate, 0.0)


if __name__ == '__main__':
    unittest.main()
