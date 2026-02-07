"""
Contention monitoring and diagnostics.

Tracks lock contention, identifies hot spots, and provides recommendations
for optimization.
"""

import threading
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


class ContentionLevel(Enum):
    """Severity levels for contention."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ContentionMetrics:
    """Metrics for a single lock."""
    name: str
    total_acquisitions: int = 0
    total_wait_time: float = 0.0
    total_hold_time: float = 0.0
    failed_attempts: int = 0
    contention_count: int = 0  # Times lock was already held
    
    @property
    def average_wait_time(self) -> float:
        """Average time spent waiting for lock."""
        if self.total_acquisitions == 0:
            return 0.0
        return self.total_wait_time / self.total_acquisitions
    
    @property
    def average_hold_time(self) -> float:
        """Average time lock is held."""
        if self.total_acquisitions == 0:
            return 0.0
        return self.total_hold_time / self.total_acquisitions
    
    @property
    def contention_rate(self) -> float:
        """Percentage of acquisitions with contention."""
        if self.total_acquisitions == 0:
            return 0.0
        return (self.contention_count / self.total_acquisitions) * 100
    
    @property
    def contention_level(self) -> ContentionLevel:
        """Determine contention severity."""
        rate = self.contention_rate
        if rate == 0:
            return ContentionLevel.NONE
        elif rate < 10:
            return ContentionLevel.LOW
        elif rate < 25:
            return ContentionLevel.MODERATE
        elif rate < 50:
            return ContentionLevel.HIGH
        else:
            return ContentionLevel.CRITICAL


@dataclass
class ContentionStats:
    """Statistics from contention monitoring."""
    total_locks_tracked: int = 0
    metrics: Dict[str, ContentionMetrics] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def get_hot_locks(self, threshold: float = 20.0) -> List[Tuple[str, ContentionMetrics]]:
        """Get locks with contention above threshold."""
        return [
            (name, metrics)
            for name, metrics in self.metrics.items()
            if metrics.contention_rate >= threshold
        ]
    
    def get_slowest_locks(self, limit: int = 10) -> List[Tuple[str, ContentionMetrics]]:
        """Get slowest locks by average wait time."""
        sorted_locks = sorted(
            self.metrics.items(),
            key=lambda x: x[1].average_wait_time,
            reverse=True
        )
        return sorted_locks[:limit]
    
    def print_report(self) -> None:
        """Print detailed contention report."""
        print("\n" + "="*100)
        print("CONTENTION MONITORING REPORT")
        print("="*100)
        print(f"Total locks tracked: {self.total_locks_tracked}\n")
        
        # Summary by contention level
        by_level = defaultdict(list)
        for name, metrics in self.metrics.items():
            by_level[metrics.contention_level].append((name, metrics))
        
        print("Summary by Contention Level:")
        for level in ContentionLevel:
            locks = by_level[level]
            if locks:
                print(f"  {level.value.upper()}: {len(locks)} lock(s)")
        
        # Hot locks
        hot_locks = self.get_hot_locks(20.0)
        if hot_locks:
            print("\n" + "-"*100)
            print("🔴 HOT LOCKS (>20% contention):")
            print("-"*100)
            for name, metrics in hot_locks:
                print(f"\n  {name}")
                print(f"    Acquisitions: {metrics.total_acquisitions}")
                print(f"    Contention rate: {metrics.contention_rate:.1f}%")
                print(f"    Avg wait time: {metrics.average_wait_time*1000:.2f}ms")
                print(f"    Avg hold time: {metrics.average_hold_time*1000:.2f}ms")
                print(f"    💡 Suggestion: Consider lock-free data structure or reduce critical section")
        
        # Slowest locks
        slowest = self.get_slowest_locks(5)
        if slowest:
            print("\n" + "-"*100)
            print("⏱️  SLOWEST LOCKS (by wait time):")
            print("-"*100)
            for name, metrics in slowest:
                if metrics.total_acquisitions > 0:
                    print(f"\n  {name}")
                    print(f"    Avg wait: {metrics.average_wait_time*1000:.2f}ms")
                    print(f"    Avg hold: {metrics.average_hold_time*1000:.2f}ms")


class ContentionMonitor:
    """
    Monitors lock contention in concurrent code.
    
    Tracks:
    - Lock acquisition attempts
    - Wait times
    - Hold times
    - Contention rates
    - Identifies hot spots
    """
    
    _instance: Optional["ContentionMonitor"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "ContentionMonitor":
        """Singleton implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the contention monitor."""
        if self._initialized:
            return
        
        self._metrics: Dict[str, ContentionMetrics] = {}
        self._enabled = False
        self._lock_stack: Dict[int, List[Tuple[str, float]]] = defaultdict(list)
        self._initialized = True
    
    def enable(self) -> None:
        """Enable contention monitoring."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable contention monitoring."""
        self._enabled = False
    
    def track_acquisition(
        self,
        lock_name: str,
        acquired: bool,
        wait_time: float = 0.0,
    ) -> None:
        """
        Record a lock acquisition attempt.
        
        Args:
            lock_name: Name of the lock
            acquired: Whether lock was successfully acquired
            wait_time: Time spent waiting for lock
        """
        if not self._enabled:
            return
        
        if lock_name not in self._metrics:
            self._metrics[lock_name] = ContentionMetrics(name=lock_name)
        
        metrics = self._metrics[lock_name]
        if acquired:
            metrics.total_acquisitions += 1
            metrics.total_wait_time += wait_time
            
            # Record the start time for hold time tracking
            thread_id = threading.get_ident()
            self._lock_stack[thread_id].append((lock_name, time.time()))
        else:
            metrics.failed_attempts += 1
    
    def track_release(self, lock_name: str, hold_time: float = 0.0) -> None:
        """
        Record a lock release.
        
        Args:
            lock_name: Name of the lock
            hold_time: Time lock was held
        """
        if not self._enabled:
            return
        
        if lock_name in self._metrics:
            self._metrics[lock_name].total_hold_time += hold_time
    
    def track_contention(self, lock_name: str) -> None:
        """
        Record that a lock had contention.
        
        Args:
            lock_name: Name of the lock
        """
        if not self._enabled:
            return
        
        if lock_name not in self._metrics:
            self._metrics[lock_name] = ContentionMetrics(name=lock_name)
        
        self._metrics[lock_name].contention_count += 1
    
    def get_stats(self) -> ContentionStats:
        """Get current monitoring statistics."""
        return ContentionStats(
            total_locks_tracked=len(self._metrics),
            metrics=self._metrics.copy(),
        )
    
    def clear(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()
        self._lock_stack.clear()
    
    def print_report(self) -> None:
        """Print contention report."""
        stats = self.get_stats()
        stats.print_report()


# Global monitor instance
_monitor = ContentionMonitor()


def get_monitor() -> ContentionMonitor:
    """Get the global contention monitor."""
    return _monitor
