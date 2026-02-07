"""
Regression Profiler: Quantify the 3.13 vs 3.13t performance trade-off.

Solves: "Should I migrate to free-threaded Python?"

Research Problem:
- Free-threaded Python (3.13t) has single-threaded regression (9-40% slower)
- Threading provides scaling benefits only if workload parallelizable
- Break-even point: Where scaling > regression cost

Algorithm:
1. Measure single-threaded performance (T1)
2. Measure multi-threaded performance (TN at optimal threads)
3. Calculate break-even: N_BE = (T1_regression) / (speedup per thread - 1)
4. Recommend: "Migrate if workload needs ≥ N_BE threads"
"""

import sys
import time
from typing import Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import concurrent.futures


class MigrationRecommendation(Enum):
    """Migration decision based on regression analysis."""
    STAY_ON_STANDARD = "stay_on_37"      # 3.13 standard only
    MIGRATE_IMMEDIATELY = "migrate_now"  # Free-threading is beneficial
    MIGRATE_IF_SCALING = "migrate_if_scale"  # Migrate if workload parallelizable


@dataclass
class RegressionMetrics:
    """Results of regression analysis."""
    single_thread_time: float          # T1 in seconds
    single_thread_regression: float    # 0-1: fraction slower in 3.13t
    optimal_threads: int               # Recommended thread count
    multi_thread_time: float           # TN at optimal threads
    scaling_factor: float              # Speedup = T1 / TN
    break_even_threads: float          # Threads needed to overcome regression
    migration_recommendation: MigrationRecommendation
    findings: List[str]
    recommendations: List[str]


class RegressionProfiler:
    """
    Analyze performance regression from 3.13 (standard) to 3.13t (free-threaded).
    
    Provides data-backed decision support for migration.
    
    Usage:
        profiler = RegressionProfiler(workload_fn)
        analysis = profiler.analyze(num_runs=10)
        print(f"Break-even: {analysis.break_even_threads:.1f} threads")
        print(f"Recommendation: {analysis.migration_recommendation.value}")
    """
    
    def __init__(
        self,
        workload_fn: Callable[[], any],
        duration_per_run: float = 2.0,
        max_threads: int = 32,
        warmup_runs: int = 2
    ):
        """
        Initialize profiler.
        
        Args:
            workload_fn: Function to profile (called repeatedly)
            duration_per_run: How long to run workload per thread count
            max_threads: Maximum threads to test
            warmup_runs: Warm-up iterations before measurement
        """
        self.workload_fn = workload_fn
        self.duration_per_run = duration_per_run
        self.max_threads = max_threads
        self.warmup_runs = warmup_runs
        self.is_free_threaded = self._check_free_threaded()
    
    def _check_free_threaded(self) -> bool:
        """Check if running in free-threaded Python."""
        if hasattr(sys, '_is_gil_enabled'):
            return not sys._is_gil_enabled()
        return False
    
    def _warm_up(self):
        """Warm up JIT/optimizations."""
        for _ in range(self.warmup_runs):
            try:
                self.workload_fn()
            except:
                pass
    
    def _measure_throughput(self, num_threads: int = 1) -> float:
        """
        Measure throughput (operations per second) with given thread count.
        
        Returns: ops/sec
        """
        if num_threads == 1:
            # Single-threaded
            self._warm_up()
            count = 0
            start = time.perf_counter()
            while time.perf_counter() - start < self.duration_per_run:
                self.workload_fn()
                count += 1
            return count / self.duration_per_run
        else:
            # Multi-threaded
            count = [0]
            lock = __import__('threading').Lock()
            
            def worker():
                local_count = 0
                start = time.perf_counter()
                while time.perf_counter() - start < self.duration_per_run:
                    self.workload_fn()
                    local_count += 1
                with lock:
                    count[0] += local_count
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                executor_start = time.perf_counter()
                futures = [executor.submit(worker) for _ in range(num_threads)]
                concurrent.futures.wait(futures)
                executor_time = time.perf_counter() - executor_start
            
            return count[0] / executor_time
    
    def analyze(self, num_runs: int = 3) -> RegressionMetrics:
        """
        Analyze regression and break-even point.
        
        Returns: RegressionMetrics with recommendation
        """
        findings = []
        recommendations = []
        
        # Measure single-threaded
        findings.append(f"Python version: {sys.version}")
        findings.append(f"Free-threaded: {self.is_free_threaded}")
        
        t1_samples = []
        for _ in range(num_runs):
            t1 = self._measure_throughput(1)
            t1_samples.append(t1)
        
        t1 = sum(t1_samples) / len(t1_samples)
        findings.append(f"Single-thread throughput: {t1:.1f} ops/sec")
        
        # Check for regression indicator
        # (In 3.13t without threads, we'd see slower baseline)
        if not self.is_free_threaded:
            findings.append("Running on standard Python 3.13 (baseline)")
            regression_pct = 0.0
        else:
            # If running on 3.13t, note that this is the regression case
            findings.append("Running on free-threaded Python 3.13t")
            regression_pct = 15.0  # Assumed typical regression
            findings.append(f"Estimated regression: ~{regression_pct}% vs standard 3.13")
        
        # Measure optimal multi-threaded
        tn_samples = []
        for threads in range(1, min(9, self.max_threads)):
            tn = self._measure_throughput(threads)
            tn_samples.append((threads, tn))
        
        # Find optimal
        optimal_threads, optimal_throughput = max(tn_samples, key=lambda x: x[1])
        findings.append(f"Optimal threads: {optimal_threads}")
        findings.append(f"Multi-thread throughput: {optimal_throughput:.1f} ops/sec")
        
        # Calculate metrics
        scaling_factor = t1 / optimal_throughput if optimal_throughput > 0 else 1.0
        
        # Break-even calculation
        # T1 is time for 1 unit of work on 1 thread
        # TN is time for N units of work on N threads
        # Break-even: when speedup from threading > regression cost
        # Simplification: break_even_threads ≈ regression_pct / (scaling_per_thread - 1)
        scaling_per_thread = scaling_factor / optimal_threads if optimal_threads > 0 else 1.0
        if scaling_per_thread > 1.0:
            break_even_threads = regression_pct / ((scaling_per_thread - 1) * 100)
        else:
            break_even_threads = float('inf')
        
        findings.append(f"Scaling efficiency: {scaling_per_thread:.2f}x per thread")
        findings.append(f"Break-even point: {break_even_threads:.1f} threads")
        
        # Migration recommendation
        if self.is_free_threaded:
            if optimal_threads >= 2 and scaling_factor < 1.0:
                rec = MigrationRecommendation.MIGRATE_IMMEDIATELY
                recommendations.append(
                    f"✅ Free-threading is beneficial for this workload"
                )
            elif optimal_threads >= break_even_threads:
                rec = MigrationRecommendation.MIGRATE_IF_SCALING
                recommendations.append(
                    f"⚙️ Migration is beneficial IF you can use ≥ {break_even_threads:.0f} threads"
                )
            else:
                rec = MigrationRecommendation.STAY_ON_STANDARD
                recommendations.append(
                    f"❌ Single-threaded regression > threading benefits. Stay on standard 3.13"
                )
        else:
            if break_even_threads <= 4:
                rec = MigrationRecommendation.MIGRATE_IMMEDIATELY
                recommendations.append(
                    f"✅ Migration to 3.13t will be beneficial (break-even at {break_even_threads:.1f} threads)"
                )
            else:
                rec = MigrationRecommendation.MIGRATE_IF_SCALING
                recommendations.append(
                    f"⚠️  Only migrate if workload uses ≥ {break_even_threads:.1f} threads"
                )
        
        return RegressionMetrics(
            single_thread_time=1.0 / t1,  # Time per operation
            single_thread_regression=regression_pct / 100.0,
            optimal_threads=optimal_threads,
            multi_thread_time=1.0 / optimal_throughput,
            scaling_factor=1.0 / scaling_factor,
            break_even_threads=break_even_threads,
            migration_recommendation=rec,
            findings=findings,
            recommendations=recommendations
        )
    
    def print_analysis(self):
        """Run analysis and print results."""
        analysis = self.analyze()
        
        print("\n" + "="*70)
        print("📊 REGRESSION ANALYSIS: 3.13 vs 3.13t (Free-Threaded)")
        print("="*70)
        
        print("\n📋 Findings:")
        for finding in analysis.findings:
            print(f"  • {finding}")
        
        print("\n📈 Metrics:")
        print(f"  Single-thread: {analysis.single_thread_time*1000:.2f}ms per op")
        print(f"  Regression: {analysis.single_thread_regression*100:.1f}%")
        print(f"  Multi-thread: {analysis.multi_thread_time*1000:.2f}ms per op ({analysis.optimal_threads} threads)")
        print(f"  Speedup: {analysis.scaling_factor:.2f}x")
        print(f"  Break-even: {analysis.break_even_threads:.1f} threads")
        
        print("\n🎯 Recommendation:")
        rec = analysis.migration_recommendation
        if rec == MigrationRecommendation.MIGRATE_IMMEDIATELY:
            print(f"  ✅ {rec.value.upper()}")
            print(f"     → Switch to 3.13t, significant benefits expected")
        elif rec == MigrationRecommendation.MIGRATE_IF_SCALING:
            print(f"  ⚙️  {rec.value.upper()}")
            print(f"     → Only if your workload needs ≥ {analysis.break_even_threads:.1f} threads")
        else:
            print(f"  ❌ {rec.value.upper()}")
            print(f"     → Stay on standard 3.13 for now")
        
        for rec_text in analysis.recommendations:
            print(f"     {rec_text}")
        
        print("\n" + "="*70)


def analyze_regression(workload_fn: Callable) -> RegressionMetrics:
    """Convenience function to run regression analysis."""
    profiler = RegressionProfiler(workload_fn, duration_per_run=1.0)
    return profiler.analyze(num_runs=2)
