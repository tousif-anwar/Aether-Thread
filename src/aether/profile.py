"""
Saturation Cliff Profiler: Detect when adding threads makes code slower.

In free-threaded Python, there's often a "saturation cliff" - a point where
adding more threads actually DECREASES performance due to contention.

This profiler:
1. Runs a workload with varying thread counts (1, 2, 4, 8, ..., N)
2. Tracks throughput and P99 latency
3. Identifies the cliff point (>= 20% performance drop)
4. Recommends optimal thread count
"""

import time
import threading
from typing import Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import statistics


@dataclass
class WorkloadMetrics:
    """Metrics from a single workload run."""
    thread_count: int
    duration_seconds: float
    operations_completed: int
    throughput: float  # ops/sec
    latencies: List[float] = field(default_factory=list)  # P99 latencies
    
    @property
    def p99_latency(self) -> float:
        """P99 latency in milliseconds."""
        if len(self.latencies) < 100:
            return max(self.latencies) * 1000 if self.latencies else 0
        sorted_lats = sorted(self.latencies)
        idx = int(len(sorted_lats) * 0.99)
        return sorted_lats[idx] * 1000
    
    @property
    def p50_latency(self) -> float:
        """Median latency in milliseconds."""
        if not self.latencies:
            return 0
        return statistics.median(self.latencies) * 1000


@dataclass
class SaturationAnalysis:
    """Analysis of saturation cliff."""
    optimal_threads: int
    cliff_threads: Optional[int]  # Where cliff occurs
    cliff_severity: float  # 0-1, how bad the drop is
    throughput_peak: float
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class SaturationCliffProfiler:
    """
    Profiles a workload to find the saturation cliff.
    
    The saturation cliff is defined as a point where throughput
    decreases by >= 20% compared to peak, despite adding more threads.
    """
    
    def __init__(self, workload_fn: Callable[[], None], 
                 duration_per_run: float = 5.0,
                 max_threads: int = 128):
        """
        Args:
            workload_fn: Callable that performs the work (e.g., lambda: process_item())
            duration_per_run: How long to run each test (seconds)
            max_threads: Maximum threads to test
        """
        self.workload_fn = workload_fn
        self.duration_per_run = duration_per_run
        self.max_threads = max_threads
        self.results: Dict[int, WorkloadMetrics] = {}
        
    def run_workload(self, num_threads: int) -> WorkloadMetrics:
        """Run workload with specified number of threads."""
        start_time = time.time()
        end_time = start_time + self.duration_per_run
        operations = [0]  # Mutable counter
        latencies = []
        lock = threading.Lock()
        
        def worker():
            """Worker thread that runs workload."""
            while time.time() < end_time:
                op_start = time.time()
                self.workload_fn()
                op_time = time.time() - op_start
                
                latencies.append(op_time)
                with lock:
                    operations[0] += 1
        
        # Run with thread pool
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        duration = time.time() - start_time
        throughput = operations[0] / duration if duration > 0 else 0
        
        return WorkloadMetrics(
            thread_count=num_threads,
            duration_seconds=duration,
            operations_completed=operations[0],
            throughput=throughput,
            latencies=latencies
        )
    
    def profile(self) -> SaturationAnalysis:
        """Run profiling across thread counts and analyze."""
        # Test exponentially increasing thread counts
        thread_counts = [1]
        current = 2
        while current <= self.max_threads:
            thread_counts.append(current)
            current *= 2
        
        print(f"🔍 Profiling workload with thread counts: {thread_counts}")
        
        for num_threads in thread_counts:
            print(f"  ▶ Testing with {num_threads} thread(s)...", end=" ", flush=True)
            metrics = self.run_workload(num_threads)
            self.results[num_threads] = metrics
            print(f"✓ {metrics.throughput:.1f} ops/sec (P99: {metrics.p99_latency:.1f}ms)")
        
        # Analyze results
        return self._analyze_cliff()
    
    def _analyze_cliff(self) -> SaturationAnalysis:
        """Analyze results to find saturation cliff."""
        if not self.results:
            return SaturationAnalysis(optimal_threads=1)
        
        sorted_results = sorted(self.results.items())
        throughputs = [m.throughput for _, m in sorted_results]
        peak_throughput = max(throughputs)
        optimal_threads = sorted_results[throughputs.index(peak_throughput)][0]
        
        # Find cliff (20% drop from peak)
        cliff_threshold = peak_throughput * 0.8
        cliff_threads = None
        cliff_severity = 0.0
        
        for thread_count, metrics in sorted_results:
            if metrics.throughput < cliff_threshold:
                if cliff_threads is None:
                    cliff_threads = thread_count
                severity = 1.0 - (metrics.throughput / peak_throughput)
                cliff_severity = max(cliff_severity, severity)
        
        # Generate findings and recommendations
        findings = []
        recommendations = []
        
        if cliff_threads:
            findings.append(f"🔴 SATURATION CLIFF DETECTED at {cliff_threads} threads")
            findings.append(f"   Performance drop: {cliff_severity*100:.1f}%")
            recommendations.append(f"⚠️ Do NOT use more than {optimal_threads} threads")
        else:
            findings.append(f"✅ No saturation cliff detected in tested range")
        
        findings.append(f"📊 Peak throughput: {peak_throughput:.1f} ops/sec at {optimal_threads} threads")
        
        # P99 latency analysis
        optimal_metrics = self.results[optimal_threads]
        if cliff_threads and cliff_threads in self.results:
            cliff_metrics = self.results[cliff_threads]
            latency_increase = cliff_metrics.p99_latency / optimal_metrics.p99_latency
            findings.append(f"⏱️  P99 latency at cliff: {latency_increase:.1f}x increase")
            recommendations.append(f"📈 Consider using {optimal_threads} threads to keep P99 < {optimal_metrics.p99_latency:.1f}ms")
        
        return SaturationAnalysis(
            optimal_threads=optimal_threads,
            cliff_threads=cliff_threads,
            cliff_severity=cliff_severity,
            throughput_peak=peak_throughput,
            findings=findings,
            recommendations=recommendations
        )
    
    def plot_results(self) -> str:
        """Generate ASCII plot ofresults."""
        if not self.results:
            return "No results to plot"
        
        sorted_results = sorted(self.results.items())
        throughputs = [m.throughput for _, m in sorted_results]
        thread_counts = [c for c, _ in sorted_results]
        
        # Normalize for ASCII plot
        max_tp = max(throughputs)
        plot_height = 20
        
        lines = ["\n📊 Saturation Cliff Profile:"]
        lines.append("Throughput vs Thread Count\n")
        
        for h in range(plot_height, 0, -1):
            threshold = (h / plot_height) * max_tp
            line = f"  {h*5:3d}% │"
            for i, tp in enumerate(throughputs):
                if tp >= threshold:
                    line += " ▓"
                else:
                    line += " │"
            lines.append(line)
        
        lines.append("      └" + "─" * (len(throughputs) * 2))
        threads_line = "       "
        for tc in thread_counts:
            threads_line += f"{tc:2d}"
        lines.append(threads_line)
        
        return "\n".join(lines)


def benchmark_function(fn: Callable, iterations: int = 1000, 
                      max_threads: int = 64) -> SaturationAnalysis:
    """
    Convenience function to benchmark a function and find saturation cliff.
    
    Args:
        fn: Function to benchmark (should be fast, e.g., < 1ms)
        iterations: How many times to call fn per run
        max_threads: Upper limit for thread testing
    
    Returns:
        SaturationAnalysis with optimal thread count and cliff recommendations
    """
    def workload():
        for _ in range(iterations):
            fn()
    
    profiler = SaturationCliffProfiler(workload, max_threads=max_threads)
    return profiler.profile()
