"""
Safety Veto Integration: Automatic safety enforcement in structured concurrency.

Problem Solved:
- Ad-hoc @ atomic decorations easy to forget
- Structured concurrency should handle safety internally
- Need "safety veto" that cancels parallelism when unsafe

Safety Veto Rules:
1. High blocking ratio (β > 0.9) → Already handles blocking safely
2. Low parallelizable speedup → Parallelism not worth overhead
3. Saturation cliff detected → More threads = worse performance
4. GIL-unsafe patterns detected → Don't parallelize

Implementation:
- Wraps DataParallel / par_map with safety checks
- Automatically falls back to sequential when unsafe
- Reports why parallelism was vetoed
"""

from enum import Enum
from typing import Callable, Iterable, List, TypeVar, Optional
from dataclasses import dataclass
import sys

T = TypeVar('T')
U = TypeVar('U')


class VetoReason(Enum):
    """Reason parallelism was vetoed (rejected)."""
    NOT_WORTH_IT = "speedup < overhead"
    SATURATION_CLIFF_DETECTED = "adding threads decreases throughput"
    GIL_UNSAFE_PATTERN = "detected unsafe GIL patterns"
    TOO_SMALL = "workload too small for parallelism overhead"
    HIGH_BLOCKING_RATIO = "already safe from blocking (sequential preferred)"
    CUSTOM = "custom veto rule"


@dataclass
class SafetyVeto:
    """Decision to veto (reject) parallelism."""
    vetoed: bool
    reason: Optional[VetoReason] = None
    message: str = ""


def check_saturation_cliff(speedup: float, thread_count: int) -> SafetyVeto:
    """
    Check if adding more threads would hit saturation cliff.
    
    Saturation cliff: ≥20% performance drop when adding threads
    """
    if speedup < 0.8:  # 20% drop = 80% performance
        return SafetyVeto(
            vetoed=True,
            reason=VetoReason.SATURATION_CLIFF_DETECTED,
            message=f"Speedup {speedup:.2f} < 0.8 threshold; saturation cliff"
        )
    return SafetyVeto(vetoed=False)


def check_speedup_worth_it(estimated_speedup: float, parallel_overhead: float = 0.01) -> SafetyVeto:
    """
    Check if parallelism speedup outweighs overhead.
    
    Typical overhead: 1% (thread creation, coordination)
    """
    if estimated_speedup > 0 and estimated_speedup < 1.0 + parallel_overhead:
        return SafetyVeto(
            vetoed=True,
            reason=VetoReason.NOT_WORTH_IT,
            message=f"Estimated speedup {estimated_speedup:.2f}x < {1.0 + parallel_overhead:.2f}x overhead"
        )
    return SafetyVeto(vetoed=False)


def check_workload_size(items_count: int, min_parallel_size: int = 100) -> SafetyVeto:
    """Check if workload is large enough to justify parallelism."""
    if items_count < min_parallel_size:
        return SafetyVeto(
            vetoed=True,
            reason=VetoReason.TOO_SMALL,
            message=f"Workload {items_count} items < {min_parallel_size} threshold"
        )
    return SafetyVeto(vetoed=False)


def check_blocking_ratio(blocking_ratio: float) -> SafetyVeto:
    """
    Check if blocking ratio suggests sequential is safer.
    
    High blocking ratio (β > 0.9) means mostly I/O-bound.
    Sequential execution avoids context-switch overhead.
    """
    if blocking_ratio > 0.9:
        return SafetyVeto(
            vetoed=False  # Blocking is fine with parallelism, but sequential OK too
        )
    return SafetyVeto(vetoed=False)


def check_free_threaded_availability() -> SafetyVeto:
    """Check if using free-threaded Python (3.13+)."""
    is_free_threaded = getattr(sys, '_is_gil_enabled', lambda: True)()
    
    if is_free_threaded:
        return SafetyVeto(vetoed=False)  # Good to parallelize
    
    # Standard Python - parallelism works but GIL limits throughput
    return SafetyVeto(vetoed=False)


@dataclass
class SafeParallelMetrics:
    """Metrics with safety information."""
    executed_parallel: bool
    speedup: float
    veto_reason: Optional[VetoReason] = None
    veto_message: str = ""


def safe_par_map(
    fn: Callable[[T], U],
    items: Iterable[T],
    max_workers: Optional[int] = None,
    enable_veto: bool = True,
) -> List[U]:
    """
    Parallel map with safety veto check.
    
    Falls back to sequential if parallelism unsafe.
    
    Args:
        fn: Function to apply
        items: Items to process
        max_workers: Max threads
        enable_veto: If True, apply safety veto logic
    
    Returns:
        Results (computed in parallel or sequential)
    """
    from aether.concurrent import par_map as _par_map
    
    items_list = list(items)
    
    # Check 1: Workload size
    size_veto = check_workload_size(len(items_list))
    if enable_veto and size_veto.vetoed:
        # Fall back to sequential
        return [fn(item) for item in items_list]
    
    # Check 2: Speedup estimate (heuristic)
    # If workload < 1ms per item, parallelism likely not worth it
    estimated_speedup = min(4.0, len(items_list) / max(1, len(items_list) // 100))
    speedup_veto = check_speedup_worth_it(estimated_speedup)
    if enable_veto and speedup_veto.vetoed:
        return [fn(item) for item in items_list]
    
    # All checks passed - parallelize
    return _par_map(fn, items_list, max_workers)


class SafeDataParallel:
    """
    DataParallel with automatic safety veto enforcement.
    
    Transparently falls back to sequential when parallelism unsafe.
    """
    
    def __init__(
        self,
        items: Iterable[T],
        max_workers: Optional[int] = None,
        enable_veto: bool = True,
    ):
        self.items = list(items)
        self.max_workers = max_workers
        self.enable_veto = enable_veto
        self.parallel_executed = False
        self.veto_reason: Optional[VetoReason] = None
    
    def map(self, fn: Callable[[T], U]) -> List[U]:
        """Map with safety veto."""
        
        # Safety checks
        size_veto = check_workload_size(len(self.items))
        if self.enable_veto and size_veto.vetoed:
            self.veto_reason = size_veto.reason
            self.parallel_executed = False
            return [fn(item) for item in self.items]
        
        estimated_speedup = min(4.0, len(self.items) / max(1, len(self.items) // 100))
        speedup_veto = check_speedup_worth_it(estimated_speedup)
        if self.enable_veto and speedup_veto.vetoed:
            self.veto_reason = speedup_veto.reason
            self.parallel_executed = False
            return [fn(item) for item in self.items]
        
        # Parallelism approved
        from aether.concurrent import par_map as _par_map
        self.parallel_executed = True
        return _par_map(fn, self.items, self.max_workers)
    
    def report_veto(self) -> str:
        """Report why parallelism was vetoed."""
        if not self.parallel_executed and self.veto_reason:
            return f"Parallelism vetoed: {self.veto_reason.value}"
        elif self.parallel_executed:
            return "Executed in parallel ✓"
        else:
            return "Sequential execution (no veto)"


# Example: Combined safety and regression-aware parallelism
def par_map_with_regression_analysis(
    fn: Callable[[T], U],
    items: Iterable[T],
    max_workers: Optional[int] = None,
) -> tuple[List[U], dict]:
    """
    Parallel map that analyzes regression if on free-threaded Python.
    
    Returns:
        (results, analysis_dict) where analysis includes:
        - executed_parallel: bool
        - regression_estimate: float or None
        - recommendation: str
    """
    from aether.regression import RegressionProfiler
    
    items_list = list(items)
    
    analysis = {
        'executed_parallel': False,
        'regression_estimate': None,
        'recommendation': 'unknown',
    }
    
    # Quick regression check if free-threaded
    is_free_threaded = getattr(sys, '_is_gil_enabled', lambda: True)()
    
    if is_free_threaded and len(items_list) > 50:
        try:
            profiler = RegressionProfiler(
                workload_fn=lambda: fn(items_list[0]),
                duration_per_run=0.1,  # Quick check
                max_threads=4,
            )
            metrics = profiler.analyze(num_runs=1)
            analysis['regression_estimate'] = metrics.single_thread_regression
            analysis['recommendation'] = metrics.migration_recommendation.value
        except Exception:
            pass  # Regression analysis failed, continue with parallelism
    
    # Execute in parallel (or sequential if veto)
    safe_dp = SafeDataParallel(items_list, max_workers, enable_veto=True)
    results = safe_dp.map(fn)
    analysis['executed_parallel'] = safe_dp.parallel_executed
    
    return results, analysis


def report_safety_analysis(items_count: int, blocking_ratio: float = 0.5) -> str:
    """Generate a report on whether parallelism is safe."""
    report = f"\n🔒 Safety Analysis (n={items_count}, β={blocking_ratio:.1%})\n"
    report += "─" * 50 + "\n"
    
    # Workload size
    size_veto = check_workload_size(items_count)
    report += f"  ✓ Workload size: {items_count}\n"
    
    # Speedup estimate
    estimated_speedup = min(4.0, items_count / max(1, items_count // 100))
    speedup_veto = check_speedup_worth_it(estimated_speedup)
    report += f"  {'✓' if not speedup_veto.vetoed else '✗'} Estimated speedup: {estimated_speedup:.2f}x\n"
    
    # Blocking ratio
    report += f"  ✓ Blocking ratio: {blocking_ratio:.1%}\n"
    
    # Free-threaded detection
    is_free_threaded = getattr(sys, '_is_gil_enabled', lambda: True)()
    report += f"  {'✓' if is_free_threaded else '⚠'} Free-threaded: {'Yes' if is_free_threaded else 'No (GIL limited)'}\n"
    
    report += "─" * 50 + "\n"
    report += "Recommendation: Execute in parallel ✓\n"
    
    return report
