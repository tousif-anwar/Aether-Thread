"""
Core benchmarking functionality for measuring concurrency performance.
"""

import time
import threading
import sys
from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    name: str
    total_time: float
    operations: int
    ops_per_second: float
    threads: int
    gil_enabled: bool
    python_version: str
    details: Dict[str, Any] = field(default_factory=dict)


class Benchmarker:
    """
    Benchmark suite for measuring concurrent performance.
    """
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
    @staticmethod
    def get_gil_status() -> bool:
        """Check if GIL is enabled."""
        if sys.version_info >= (3, 13):
            return sys._is_gil_enabled()
        return True
    
    def run_concurrent_benchmark(
        self,
        name: str,
        func: Callable,
        num_threads: int,
        num_operations: int
    ) -> BenchmarkResult:
        """Run a concurrent benchmark with multiple threads."""
        ops_per_thread = num_operations // num_threads
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads):
                start_op = i * ops_per_thread
                end_op = start_op + ops_per_thread
                future = executor.submit(
                    self._run_operations,
                    func,
                    start_op,
                    end_op
                )
                futures.append(future)
            
            for future in as_completed(futures):
                future.result()
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        ops_per_second = num_operations / total_time if total_time > 0 else 0
        
        result = BenchmarkResult(
            name=name,
            total_time=total_time,
            operations=num_operations,
            ops_per_second=ops_per_second,
            threads=num_threads,
            gil_enabled=self.get_gil_status(),
            python_version=self.python_version,
        )
        
        self.results.append(result)
        return result
    
    def run_sequential_benchmark(
        self,
        name: str,
        func: Callable,
        num_operations: int
    ) -> BenchmarkResult:
        """Run a sequential benchmark (single-threaded baseline)."""
        start_time = time.perf_counter()
        self._run_operations(func, 0, num_operations)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        ops_per_second = num_operations / total_time if total_time > 0 else 0
        
        result = BenchmarkResult(
            name=name,
            total_time=total_time,
            operations=num_operations,
            ops_per_second=ops_per_second,
            threads=1,
            gil_enabled=self.get_gil_status(),
            python_version=self.python_version,
        )
        
        self.results.append(result)
        return result
    
    @staticmethod
    def _run_operations(func: Callable, start: int, end: int) -> None:
        """Run operations from start to end."""
        for i in range(start, end):
            func(i)
    
    def get_results(self) -> List[BenchmarkResult]:
        """Get all benchmark results."""
        return self.results
    
    def print_results(self) -> None:
        """Print formatted benchmark results."""
        if not self.results:
            print("No benchmark results to display")
            return
        
        print("\n" + "="*100)
        print("BENCHMARK RESULTS")
        print("="*100)
        print(f"Python: {self.python_version} | GIL: {'Enabled' if self.get_gil_status() else 'Disabled'}\n")
        
        print(f"{'Benchmark':<30} {'Threads':<10} {'Operations':<12} {'Time (s)':<12} {'Ops/sec':<15}")
        print("-" * 100)
        
        for result in self.results:
            print(f"{result.name:<30} {result.threads:<10} {result.operations:<12} "
                  f"{result.total_time:<12.4f} {result.ops_per_second:<15,.0f}")
        
        print("="*100)
