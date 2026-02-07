"""
Runner for benchmarking collections and patterns.
"""

from typing import Dict, Any, List
from .benchmarker import Benchmarker, BenchmarkResult
from ..proxy import ThreadSafeList, ThreadSafeDict


class BenchmarkRunner:
    """
    Runner for standard benchmarks comparing different implementations.
    """
    
    def __init__(self):
        self.benchmarker = Benchmarker()
    
    def run_list_benchmarks(self, num_ops: int = 10000) -> List[BenchmarkResult]:
        """Benchmark different list implementations."""
        results = []
        
        # Standard list - sequential
        results.append(self.benchmarker.run_sequential_benchmark(
            "StandardList-Sequential",
            lambda i: self._list_append_op([]),
            num_ops
        ))
        
        # ThreadSafe list - sequential
        safe_list = ThreadSafeList()
        results.append(self.benchmarker.run_sequential_benchmark(
            "ThreadSafeList-Sequential",
            lambda i: safe_list.append(i),
            num_ops
        ))
        
        # Standard list - concurrent (unsafe)
        results.append(self.benchmarker.run_concurrent_benchmark(
            "StandardList-Concurrent-4T",
            lambda i: self._list_append_op([]),
            num_threads=4,
            num_operations=num_ops
        ))
        
        # ThreadSafe list - concurrent
        safe_list = ThreadSafeList()
        results.append(self.benchmarker.run_concurrent_benchmark(
            "ThreadSafeList-Concurrent-4T",
            lambda i: safe_list.append(i),
            num_threads=4,
            num_operations=num_ops
        ))
        
        return results
    
    def run_dict_benchmarks(self, num_ops: int = 10000) -> List[BenchmarkResult]:
        """Benchmark different dict implementations."""
        results = []
        
        # Standard dict - sequential
        d = {}
        results.append(self.benchmarker.run_sequential_benchmark(
            "StandardDict-Sequential",
            lambda i: d.update({f"key_{i}": i}),
            num_ops
        ))
        
        # ThreadSafe dict - sequential
        safe_dict = ThreadSafeDict()
        results.append(self.benchmarker.run_sequential_benchmark(
            "ThreadSafeDict-Sequential",
            lambda i: safe_dict.update({f"key_{i}": i}),
            num_ops
        ))
        
        # Standard dict - concurrent (unsafe)
        results.append(self.benchmarker.run_concurrent_benchmark(
            "StandardDict-Concurrent-4T",
            lambda i: {f"key_{i}": i},
            num_threads=4,
            num_operations=num_ops
        ))
        
        # ThreadSafe dict - concurrent
        safe_dict = ThreadSafeDict()
        results.append(self.benchmarker.run_concurrent_benchmark(
            "ThreadSafeDict-Concurrent-4T",
            lambda i: safe_dict.update({f"key_{i}": i}),
            num_threads=4,
            num_operations=num_ops
        ))
        
        return results
    
    def run_all_benchmarks(self, num_ops: int = 10000) -> None:
        """Run all available benchmarks and print results."""
        print("\nRunning list benchmarks...")
        list_results = self.run_list_benchmarks(num_ops)
        
        print("Running dict benchmarks...")
        dict_results = self.run_dict_benchmarks(num_ops)
        
        self.benchmarker.print_results()
    
    @staticmethod
    def _list_append_op(lst: list) -> None:
        """Dummy list operation for benchmarking."""
        lst.append(None)
