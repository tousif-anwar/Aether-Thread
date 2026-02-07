"""
GIL Contention Profiler - Measures and reports on GIL-related performance issues.
"""

import sys
import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import functools


@dataclass
class ProfileEntry:
    """Represents a profiling entry for a function call."""
    
    function_name: str
    thread_id: int
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    lock_wait_time: float = 0.0


@dataclass
class ProfileReport:
    """Summary report of profiling results."""
    
    total_time: float
    function_times: Dict[str, float] = field(default_factory=dict)
    thread_times: Dict[int, float] = field(default_factory=dict)
    call_counts: Dict[str, int] = field(default_factory=dict)
    total_lock_wait: float = 0.0
    parallelism_factor: float = 1.0


class GILContentionProfiler:
    """
    Profiles Python code to measure GIL contention and threading performance.
    
    This profiler helps identify bottlenecks in multi-threaded code and
    provides insights into how effectively the code uses concurrency.
    
    Example:
        profiler = GILContentionProfiler()
        profiler.start()
        
        # Your multi-threaded code here
        
        profiler.stop()
        report = profiler.get_report()
        print(report)
    """
    
    def __init__(self) -> None:
        self.entries: List[ProfileEntry] = []
        self._active = False
        self._start_time: Optional[float] = None
        self._stop_time: Optional[float] = None
        self._lock = threading.Lock()
        
    def start(self) -> None:
        """Start profiling."""
        with self._lock:
            self._active = True
            self._start_time = time.time()
            self.entries.clear()
    
    def stop(self) -> None:
        """Stop profiling."""
        with self._lock:
            self._active = False
            self._stop_time = time.time()
    
    def profile_function(self, func: Any) -> Any:
        """
        Decorator to profile a specific function.
        
        Args:
            func: The function to profile
            
        Returns:
            Wrapped function with profiling
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self._active:
                return func(*args, **kwargs)
            
            entry = ProfileEntry(
                function_name=func.__name__,
                thread_id=threading.get_ident(),
                start_time=time.time()
            )
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                entry.end_time = time.time()
                entry.duration = entry.end_time - entry.start_time
                
                with self._lock:
                    self.entries.append(entry)
        
        return wrapper
    
    def record_lock_wait(self, duration: float) -> None:
        """
        Manually record time spent waiting for a lock.
        
        Args:
            duration: Time in seconds spent waiting
        """
        if self._active and self.entries:
            with self._lock:
                if self.entries:
                    self.entries[-1].lock_wait_time += duration
    
    def get_report(self) -> ProfileReport:
        """
        Generate a profiling report.
        
        Returns:
            ProfileReport with summary statistics
        """
        if self._start_time is None:
            return ProfileReport(total_time=0.0)
        
        total_time = (self._stop_time or time.time()) - self._start_time
        
        function_times: Dict[str, float] = defaultdict(float)
        thread_times: Dict[int, float] = defaultdict(float)
        call_counts: Dict[str, int] = defaultdict(int)
        total_lock_wait = 0.0
        
        for entry in self.entries:
            if entry.duration is not None:
                function_times[entry.function_name] += entry.duration
                thread_times[entry.thread_id] += entry.duration
                call_counts[entry.function_name] += 1
                total_lock_wait += entry.lock_wait_time
        
        # Calculate parallelism factor
        total_cpu_time = sum(function_times.values())
        parallelism_factor = total_cpu_time / total_time if total_time > 0 else 1.0
        
        return ProfileReport(
            total_time=total_time,
            function_times=dict(function_times),
            thread_times=dict(thread_times),
            call_counts=dict(call_counts),
            total_lock_wait=total_lock_wait,
            parallelism_factor=parallelism_factor
        )
    
    def print_report(self) -> None:
        """Print a formatted profiling report."""
        report = self.get_report()
        
        print("\n" + "=" * 60)
        print("GIL Contention Profiler Report")
        print("=" * 60)
        print(f"Total Execution Time: {report.total_time:.4f} seconds")
        print(f"Total Lock Wait Time: {report.total_lock_wait:.4f} seconds")
        print(f"Parallelism Factor: {report.parallelism_factor:.2f}x")
        print(f"Number of Threads: {len(report.thread_times)}")
        
        if report.function_times:
            print("\nFunction Times:")
            print("-" * 60)
            for func_name, duration in sorted(
                report.function_times.items(), key=lambda x: x[1], reverse=True
            ):
                calls = report.call_counts[func_name]
                avg = duration / calls if calls > 0 else 0
                print(f"  {func_name:30} {duration:8.4f}s ({calls:3} calls, {avg:.4f}s avg)")
        
        if report.thread_times:
            print("\nThread Times:")
            print("-" * 60)
            for thread_id, duration in sorted(
                report.thread_times.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  Thread {thread_id:15} {duration:8.4f}s")
        
        print("=" * 60 + "\n")


def profile_with_gil(func: Any) -> Any:
    """
    Convenience decorator for quick profiling of a single function.
    
    Example:
        @profile_with_gil
        def my_function():
            # code here
            pass
    """
    profiler = GILContentionProfiler()
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        profiler.start()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.stop()
            profiler.print_report()
    
    return wrapper
