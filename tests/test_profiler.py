"""
Tests for the GIL Contention Profiler.
"""

import pytest
import time
import threading
from aether_thread.profiler import GILContentionProfiler, profile_with_gil


def test_profiler_initialization():
    """Test profiler initialization."""
    profiler = GILContentionProfiler()
    assert profiler.entries == []
    assert not profiler._active


def test_profiler_start_stop():
    """Test starting and stopping the profiler."""
    profiler = GILContentionProfiler()
    
    profiler.start()
    assert profiler._active
    assert profiler._start_time is not None
    
    profiler.stop()
    assert not profiler._active
    assert profiler._stop_time is not None


def test_profile_function_decorator():
    """Test profiling a function."""
    profiler = GILContentionProfiler()
    
    @profiler.profile_function
    def test_func():
        time.sleep(0.01)
        return 42
    
    profiler.start()
    result = test_func()
    profiler.stop()
    
    assert result == 42
    assert len(profiler.entries) == 1
    assert profiler.entries[0].function_name == 'test_func'


def test_get_report():
    """Test report generation."""
    profiler = GILContentionProfiler()
    
    @profiler.profile_function
    def worker(n):
        time.sleep(0.01)
        return n * 2
    
    profiler.start()
    worker(5)
    worker(10)
    profiler.stop()
    
    report = profiler.get_report()
    
    assert report.total_time > 0
    assert 'worker' in report.function_times
    assert report.call_counts['worker'] == 2


def test_multithreaded_profiling():
    """Test profiling with multiple threads."""
    profiler = GILContentionProfiler()
    
    @profiler.profile_function
    def thread_worker(thread_id):
        time.sleep(0.01)
        return thread_id
    
    profiler.start()
    
    threads = [
        threading.Thread(target=thread_worker, args=(i,))
        for i in range(3)
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    profiler.stop()
    
    report = profiler.get_report()
    assert len(report.thread_times) == 3
    assert report.call_counts['thread_worker'] == 3


def test_profile_with_gil_decorator():
    """Test the profile_with_gil convenience decorator."""
    @profile_with_gil
    def simple_task():
        return sum(range(100))
    
    # This should profile and print report
    result = simple_task()
    assert result == 4950


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
