"""
Example: Basic usage of Aether-Thread toolkit.

This example demonstrates how to use the analyzer, decorators, and profiler.
"""

import time
import threading
from aether_thread import (
    ThreadSafetyAnalyzer,
    thread_safe,
    gil_free_compatible,
    GILContentionProfiler,
    ThreadSafeCounter
)


# Example 1: Analyzing code for thread-safety issues
def example_analyze():
    """Demonstrate code analysis."""
    print("\n" + "=" * 60)
    print("Example 1: Code Analysis")
    print("=" * 60)
    
    # Code with potential thread-safety issues
    code_to_analyze = """
global counter
counter = 0

def increment():
    global counter
    counter += 1  # Not thread-safe!
"""
    
    analyzer = ThreadSafetyAnalyzer()
    issues = analyzer.analyze_code(code_to_analyze)
    
    print(f"\nFound {len(issues)} potential issues:")
    for issue in issues:
        print(f"  - [{issue.severity}] {issue.message}")
    
    summary = analyzer.get_summary()
    print(f"\nThread-safe: {summary['is_thread_safe']}")


# Example 2: Using thread_safe decorator
@thread_safe
def shared_counter_operation(counter_list):
    """A thread-safe operation on shared data."""
    value = counter_list[0]
    time.sleep(0.001)  # Simulate work
    counter_list[0] = value + 1


def example_thread_safe_decorator():
    """Demonstrate thread_safe decorator."""
    print("\n" + "=" * 60)
    print("Example 2: Thread-Safe Decorator")
    print("=" * 60)
    
    counter = [0]  # Using list to allow modification in function
    
    threads = [
        threading.Thread(target=shared_counter_operation, args=(counter,))
        for _ in range(10)
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print(f"\nFinal counter value: {counter[0]}")
    print("Expected: 10 (all increments were thread-safe)")


# Example 3: Using ThreadSafeCounter
def example_thread_safe_counter():
    """Demonstrate ThreadSafeCounter."""
    print("\n" + "=" * 60)
    print("Example 3: ThreadSafeCounter")
    print("=" * 60)
    
    counter = ThreadSafeCounter(0)
    
    def worker():
        for _ in range(100):
            counter.increment()
    
    threads = [threading.Thread(target=worker) for _ in range(5)]
    
    start_time = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - start_time
    
    print(f"\nFinal counter value: {counter.value}")
    print(f"Expected: 500")
    print(f"Time elapsed: {elapsed:.4f} seconds")


# Example 4: Using GIL Contention Profiler
def example_profiler():
    """Demonstrate profiling."""
    print("\n" + "=" * 60)
    print("Example 4: GIL Contention Profiler")
    print("=" * 60)
    
    profiler = GILContentionProfiler()
    
    @profiler.profile_function
    def cpu_intensive(n):
        """Simulate CPU-intensive work."""
        result = 0
        for i in range(n):
            result += i ** 2
        return result
    
    @profiler.profile_function
    def io_intensive():
        """Simulate I/O work."""
        time.sleep(0.01)
    
    profiler.start()
    
    # Run some work
    threads = []
    for i in range(3):
        t1 = threading.Thread(target=cpu_intensive, args=(10000,))
        t2 = threading.Thread(target=io_intensive)
        threads.extend([t1, t2])
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    profiler.stop()
    profiler.print_report()


# Example 5: GIL-free compatible function
@gil_free_compatible(strict=False)
def example_gil_free_function(data):
    """
    A function marked as GIL-free compatible.
    
    This function doesn't rely on GIL for thread safety.
    """
    # Pure computation, no shared state
    return sum(x ** 2 for x in data)


def example_gil_free():
    """Demonstrate GIL-free compatible marking."""
    print("\n" + "=" * 60)
    print("Example 5: GIL-Free Compatible Function")
    print("=" * 60)
    
    data = list(range(100))
    result = example_gil_free_function(data)
    
    print(f"\nResult: {result}")
    print("This function is marked as GIL-free compatible")


def main():
    """Run all examples."""
    print("\n" + "#" * 60)
    print("# Aether-Thread Toolkit Examples")
    print("#" * 60)
    
    example_analyze()
    example_thread_safe_decorator()
    example_thread_safe_counter()
    example_profiler()
    example_gil_free()
    
    print("\n" + "#" * 60)
    print("# All examples completed!")
    print("#" * 60 + "\n")


if __name__ == '__main__':
    main()
