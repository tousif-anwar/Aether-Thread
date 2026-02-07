"""
Example demonstrating Aether-Thread usage.
"""

# Example 1: Using aether-audit to detect thread-safety issues
print("=" * 80)
print("EXAMPLE 1: Thread-Safety Issue Detection")
print("=" * 80)

import tempfile
from pathlib import Path
from aether_thread.audit import StaticScanner

# Create a sample Python file with thread-safety issues
sample_code = '''
# Global mutable state - THREAD-UNSAFE!
shared_cache = {}
results_list = []

class DataProcessor:
    # Class-level mutable attribute - THREAD-UNSAFE!
    processed_items = {}
    
    def process(self, item):
        # Modifying global state without synchronization
        shared_cache[item] = True
        results_list.append(item)
        self.processed_items[item] = True
'''

# Create temporary file for scanning
with tempfile.TemporaryDirectory() as tmpdir:
    temp_file = Path(tmpdir) / "example.py"
    temp_file.write_text(sample_code)
    
    # Scan the directory
    scanner = StaticScanner()
    results = scanner.scan(tmpdir)
    scanner.print_report()

# Example 2: Using ThreadSafe collections
print("\n" + "=" * 80)
print("EXAMPLE 2: Thread-Safe Collections")
print("=" * 80)

from aether_thread.proxy import ThreadSafeList, ThreadSafeDict
import threading

# Create thread-safe list
safe_list = ThreadSafeList()

def append_numbers(start, end):
    """Worker function to append numbers to safe list."""
    for i in range(start, end):
        safe_list.append(i)

# Create and start threads
threads = []
for i in range(4):
    t = threading.Thread(target=append_numbers, args=(i * 25, (i + 1) * 25))
    threads.append(t)
    t.start()

# Wait for all threads
for t in threads:
    t.join()

print(f"ThreadSafeList: {len(safe_list)} items safely appended from 4 concurrent threads")

# Example 3: Using ThreadSafe dict
print("\nThreadSafeDict Example:")
safe_dict = ThreadSafeDict()

def update_dict(thread_id):
    """Worker function to update dict concurrently."""
    for i in range(10):
        key = f"thread_{thread_id}_item_{i}"
        safe_dict[key] = i * thread_id

threads = []
for i in range(3):
    t = threading.Thread(target=update_dict, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print(f"ThreadSafeDict: {len(safe_dict)} items safely stored from 3 concurrent threads")

# Example 4: Benchmarking
print("\n" + "=" * 80)
print("EXAMPLE 3: Benchmarking Concurrent Performance")
print("=" * 80)

from aether_thread.bench import BenchmarkRunner

runner = BenchmarkRunner()

print("\nRunning list append benchmarks...")
list_results = runner.run_list_benchmarks(num_ops=5000)

print("\nRunning dict update benchmarks...")
dict_results = runner.run_dict_benchmarks(num_ops=5000)

# Print summary
runner.benchmarker.print_results()

print("\n" + "=" * 80)
print("Examples completed successfully!")
print("=" * 80)
