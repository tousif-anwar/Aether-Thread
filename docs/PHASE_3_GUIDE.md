# Aether-Thread Phase 3.0+ Guide: Free-Threading Support

## Overview

Phase 3 of Aether-Thread adds comprehensive tools for **Python 3.13+ free-threaded (GIL-disabled) environments**. This guide covers all the new features introduced in v0.3.0 and how to use them.

---

## Table of Contents

1. [What's New in Phase 3](#whats-new)
2. [Quick Start](#quick-start)
3. [Module Reference](#module-reference)
4. [Integration Patterns](#integration-patterns)
5. [Troubleshooting](#troubleshooting)

---

## What's New in Phase 3 {#whats-new}

### Phase 3.0: Core Free-Threading Tools

#### 🟢 **Free-Thread Detector** (`aether.audit.free_thread_detector`)
Detects code patterns that are unsafe or crash in free-threaded Python.

**Threat Types:**
1. **FRAME_LOCALS_ACCESS** (🔴 Crash Risk)
   - Accessing `frame.f_locals` or `frame.f_globals` from wrong thread
   - Can crash Python interpreter in free-threaded mode
   
2. **WARNING_CATCH_CONTEXT** (🟠 Race Risk)
   - Using `warnings.catch_warnings()` without synchronization
   - Thread-race condition on global warning state

3. **SHARED_ITERATOR** (🔴 Data Loss)
   - Iterating same object from multiple threads
   - Causes duplicate/missing elements

4. **ASYNC_THREADING_MIX** (🟠 Deadlock Risk)
   - Mixing `async/await` with threading
   - Can deadlock event loop

5. **SIGNAL_HANDLER_RACE** (🔴 Critical Race)
   - Signal handlers modifying shared state
   - Atomic access required

6. **EXCEPTION_GROUP_RACE** (🟡 Consistency)
   - ExceptionGroup in threaded code
   - Exception ordering issues

#### ⚡ **Saturation Cliff Profiler** (`aether.profile`)
Finds performance cliffs—points where adding threads makes code **slower**.

**Key Concept:**
- Exponential thread scaling (1, 2, 4, 8, 16, ...)
- Tracks throughput (ops/sec) and P99 latency
- Detects ≥20% performance drops
- Recommends optimal thread count

**Why This Matters:**
```
Threads  | Throughput | Latency
---------|------------|----------
1        | 1000 ops/s | 1ms
2        | 2000 ops/s | 1ms     (linear scaling)
4        | 3900 ops/s | 1.3ms   (near-linear)
8        | 3100 ops/s | 4.2ms   ← SATURATION CLIFF
16       | 2500 ops/s | 8.1ms   (getting worse!)
```

Adding more threads after the cliff actually **decreases** performance due to:
- Lock contention
- Context switch overhead
- Cache coherency overhead

#### 🎯 **Adaptive Thread Pool** (`aether.pool`)
Auto-tuning thread pool that adapts to workload and prevents saturation cliff.

**Key Metric: Blocking Ratio (β)**
$$\beta = 1 - \frac{\text{CPU time}}{\text{Wall time}}$$

- **β ≈ 1.0** → Pure I/O (network, disk, sleep) → **Scale threads up!**
- **β ≈ 0.5** → Mixed I/O and compute → **Careful scaling**
- **β ≈ 0.0** → CPU bound or heavy locks → **Don't add threads**

The pool monitors β continuously and vetoes thread scaling when β < threshold (default 0.3).

#### ✅ **GIL Status Checker** (`aether.check`)
Verifies the Python environment and package compatibility.

**Checks:**
- Is GIL currently enabled or disabled?
- Is this a free-threaded Python build?
- Which packages are thread-safe?
- Which packages require the GIL?

### Phase 3.1: Developer Experience

#### 💻 **CLI Interface** (`aether.cli`)

Command-line tools for users who prefer not to write code.

```bash
# Check code for issues
aether check src/

# Check with free-threading specific checks
aether check src/ --free-threaded

# Deep scan
aether scan . --all

# Profile a script
aether profile benchmark.py --max-threads 64

# Check environment
aether status
```

#### 📔 **Jupyter Magics** (`aether.jupyter_magic`)

Interactive notebook commands for exploration.

```python
%load_ext aether.jupyter_magic

# Check cell code
%%audit
# your code here

# Profile cell
%%profile_threads --max-threads 32
def workload():
    pass

# Check free-threading safety
%%free_threaded_check
# your code here

# Quick GIL check
%gil_status --full
```

---

## Quick Start {#quick-start}

### Installation

```bash
# Install aether-thread with all optional dependencies
pip install aether-thread[free-threading]

# Or install manually
pip install aether-thread
pip install psutil  # Required for AdaptiveThreadPool CPU metrics
```

### Example 1: Check Code for Thread-Safety Issues

```python
from aether.audit.free_thread_detector import FreeThreadDetector

code = """
import sys
import warnings

def process_data():
    frame = sys._getframe()
    # This is dangerous in free-threaded Python!
    locals_dict = frame.f_locals
    
    with warnings.catch_warnings():
        # Not thread-safe without locks
        warnings.simplefilter("ignore")
        do_work()
"""

detector = FreeThreadDetector("mycode.py")
threats = detector.detect(code)

for threat in threats:
    print(f"{'🔴 CRASH' if threat.crash_risk else '🟠 SAFETY'}")
    print(f"  Type: {threat.threat_type.value}")
    print(f"  Issue: {threat.description}")
    print(f"  Fix: {threat.recommendation}\n")
```

**Output:**
```
🔴 CRASH
  Type: frame_locals_access
  Issue: Accessing frame.f_locals from non-owner thread
  Fix: Use threading.local() or queue.Queue instead of frame access

🟠 SAFETY
  Type: warning_catch_context
  Issue: warnings.catch_warnings() is not thread-safe
  Fix: Protect with threading.Lock or use threading-aware alarm
```

### Example 2: Find Performance Saturation Cliff

```python
from aether.profile import SaturationCliffProfiler
import time

def cpu_bound_workload():
    """CPU-intensive work (no I/O)."""
    total = 0
    for i in range(10000):
        total += i ** 2
    return total

def io_bound_workload():
    """I/O-intensive work."""
    time.sleep(0.01)  # Simulates I/O
    return "done"

# Profile CPU-bound (expects to saturate quickly)
profiler = SaturationCliffProfiler(cpu_bound_workload, max_threads=16)
cpu_analysis = profiler.profile()
print(f"CPU-bound: Optimal {cpu_analysis.optimal_threads} threads")
print(f"Cliff at {cpu_analysis.cliff_threads} threads")

# Profile I/O-bound (can scale to many threads)
profiler = SaturationCliffProfiler(io_bound_workload, max_threads=64)
io_analysis = profiler.profile()
print(f"I/O-bound: Optimal {io_analysis.optimal_threads} threads")
```

### Example 3: Use Adaptive Thread Pool

```python
from aether.pool import AdaptiveThreadPool
import time

def worker(item):
    """Process one item."""
    time.sleep(0.01)  # Simulate I/O
    return item * 2

# Use adaptive pool - it auto-tunes thread count
with AdaptiveThreadPool(max_workers=32) as pool:
    data = range(100)
    results = pool.map(worker, data)
    
    # Check how the pool adapted
    metrics = pool.get_metrics()
    print(f"Blocking ratio: {metrics.blocking_ratio:.1%}")
    print(f"Active threads: {metrics.active_threads}")
    print(f"Throughput: {metrics.throughput:.0f} ops/sec")
    print(f"Avg latency: {metrics.avg_latency_ms:.1f}ms")
    
    pool.print_status()
```

### Example 4: Check Environment

```python
from aether.check import GILStatusChecker, is_free_threaded

checker = GILStatusChecker()

if is_free_threaded():
    print("✅ Running free-threaded Python!")
    checker.print_status()
else:
    print("⚠️ Standard Python (GIL enabled)")
    print("Install Python 3.13+ with --disable-gil to use free-threading")
```

---

## Module Reference {#module-reference}

### `aether.audit.free_thread_detector`

**Main Class:** `FreeThreadDetector`

```python
from aether.audit.free_thread_detector import FreeThreadDetector, FreeThreadThreat

# Initialize
detector = FreeThreadDetector(filename="mycode.py")

# Analyze code
threats = detector.detect(source_code)

# Access findings
for threat in threats:
    threat.threat_type      # FreeThreadThreat enum
    threat.description      # Human-readable description
    threat.recommendation   # How to fix
    threat.line_number      # Line with the issue
    threat.crash_risk       # Boolean: is it a crash risk?
```

**FreeThreadThreat Enum:**
```python
class FreeThreadThreat(Enum):
    FRAME_LOCALS_ACCESS = "frame_locals_access"
    WARNING_CATCH_CONTEXT = "warning_catch_context"
    SHARED_ITERATOR = "shared_iterator"
    ASYNC_THREADING_MIX = "async_threading_mix"
    SIGNAL_HANDLER_RACE = "signal_handler_race"
    EXCEPTION_GROUP_RACE = "exception_group_race"
```

### `aether.profile`

**Main Class:** `SaturationCliffProfiler`

```python
from aether.profile import SaturationCliffProfiler

profiler = SaturationCliffProfiler(
    workload_fn,           # Callable that does work
    duration_per_run=5.0,  # Seconds per thread count test
    max_threads=128        # Maximum threads to test
)

# Run profile
analysis = profiler.profile()

# Access results
analysis.optimal_threads      # Recommended thread count
analysis.cliff_threads        # Where cliff occurs
analysis.cliff_severity       # 0-1 scale
analysis.findings             # List of issues
analysis.recommendations      # List of recommendations

# Visualize
print(analysis.plot_ascii_chart())
```

### `aether.pool`

**Main Class:** `AdaptiveThreadPool`

```python
from aether.pool import AdaptiveThreadPool, ThreadPoolMetrics

pool = AdaptiveThreadPool(
    max_workers=32,           # Max threads
    min_workers=1,            # Min threads
    blocking_threshold=0.3,   # β threshold for contention
    monitor_interval=1.0      # Check metrics every Ns
)

# Use as context manager
with pool:
    results = pool.map(fn, items)
    results = pool.submit(fn, *args).result()

# Get metrics
metrics = pool.get_metrics()
metrics.blocking_ratio    # β metric
metrics.active_threads    # Current thread count
metrics.throughput        # ops/sec
metrics.avg_latency_ms    # milliseconds
metrics.cpu_percent       # CPU utilization

# Display status
pool.print_status()
```

### `aether.check`

**Main Class:** `GILStatusChecker`

```python
from aether.check import (
    GILStatusChecker,
    GILStatus,
    EnvironmentStatus,
    get_gil_status,
    is_free_threaded
)

# Quick check
if is_free_threaded():
    print("Free-threaded mode!")

# Detailed check
checker = GILStatusChecker()
status = checker.get_status()

status.gil_status              # GILStatus enum
status.python_version          # e.g., "3.13.0"
status.is_free_threaded_build  # Boolean
status.free_threaded_packages  # List of compatible packages
status.potentially_unsafe_packages  # List to check

# Print report
checker.print_status()
```

### `aether.cli`

**Main Class:** `AetherCLI`

```bash
# Check code
aether check <path> [--free-threaded] [--verbose]

# Profile performance
aether profile <script> [--max-threads N] [--duration S]

# Environment status
aether status [--verbose]

# Deep scan
aether scan <path> [--all] [--free-threaded]
```

### `aether.jupyter_magic`

**Load Magic:**
```python
%load_ext aether.jupyter_magic
```

**Available Commands:**
- `%%audit [--verbose]` – Check cell code for issues
- `%%profile_threads [--max-threads N] [--duration S]` – Profile workload
- `%%free_threaded_check [--verbose]` – Free-threading safety check
- `%gil_status [--full]` – Show GIL/environment status

---

## Integration Patterns {#integration-patterns}

### Pattern 1: Pre-Commit Safety Check

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: aether-check
      name: Aether thread-safety check
      entry: aether check src/ --free-threaded
      language: system
      stages: [commit]
      pass_filenames: false
```

### Pattern 2: CI/CD Integration

In `.github/workflows/test.yml`:

```yaml
- name: Check thread-safety
  run: aether check src/ --free-threaded --verbose

- name: Profile performance
  run: aether profile benchmarks/workload.py --max-threads 32
```

### Pattern 3: Interactive Notebook Analysis

```python
# In Jupyter notebook
%load_ext aether.jupyter_magic

# Check your functions as you write them
%%audit
def process_user_data(user_id, shared_cache):
    # Get user data
    data = fetch_user(user_id)
    shared_cache[user_id] = data
    return data

# Profile them
%%profile_threads --max-threads 16
def workload():
    for user_id in range(100):
        process_user_data(user_id, cache)

# Check GIL status
%gil_status
```

### Pattern 4: Production Monitoring

```python
from aether.pool import AdaptiveThreadPool
from aether.check import is_free_threaded
import logging

logger = logging.getLogger(__name__)

# Use adaptive pool with monitoring
with AdaptiveThreadPool(max_workers=32) as pool:
    results = pool.map(process_item, work_items)
    
    # Log pool health
    metrics = pool.get_metrics()
    if metrics.blocking_ratio < 0.1:
        logger.warning(f"High contention detected: β={metrics.blocking_ratio:.1%}")
    
    logger.info(f"Pool used {metrics.active_threads} threads, "
                f"throughput: {metrics.throughput:.0f} ops/sec")
```

---

## Troubleshooting {#troubleshooting}

### Q: I'm getting "ModuleNotFoundError: No module named 'psutil'"

**A:** Install the optional dependency:
```bash
pip install psutil
```

The `AdaptiveThreadPool` requires `psutil` for CPU metrics. Other modules work without it.

### Q: FreeThreadDetector is detecting false positives

**A:** The detector uses AST analysis for **safety**. It flags patterns that *could* be unsafe in free-threaded Python. Review each finding:

```python
for threat in threats:
    if threat.crash_risk:
        # Definitely need to fix this
        fix_it()
    else:
        # Review: might be safe if protected by locks
        if has_locks_around_access(threat.line_number):
            # Safe to ignore
            pass
```

### Q: Saturation cliff profiler is slow

**A:** Reduce `max_threads` or `duration_per_run`:

```python
# Faster (less accurate)
profiler = SaturationCliffProfiler(
    workload,
    max_threads=16,       # Smaller range
    duration_per_run=1.0  # Shorter runs
)

# Slower but more accurate
profiler = SaturationCliffProfiler(
    workload,
    max_threads=128,      # Full range
    duration_per_run=10.0 # Longer runs
)
```

### Q: AdaptiveThreadPool isn't auto-scaling

**A:** Check the blocking ratio:

```python
metrics = pool.get_metrics()
print(f"Blocking ratio: {metrics.blocking_ratio:.1%}")

# β < 0.3 = likely lock contention, pool won't scale
# β > 0.3 = I/O bound, pool should scale

# Adjust threshold if needed:
pool = AdaptiveThreadPool(
    max_workers=32,
    blocking_threshold=0.5  # More aggressive scaling
)
```

### Q: CLI says "Python file not found"

**A:** Provide the full path or ensure file exists:

```bash
# This works
aether check ./src/mycode.py
aether check src/

# Not this
aether check mycode.py  # Wrong if not in current dir
```

---

## Migration Path: Standard Python → Free-Threading

### Step 1: Identify Issues
```bash
aether check src/ --free-threaded
```

### Step 2: Fix Critical Issues
Address all 🔴 (crash risk) findings.

### Step 3: Optimize Performance
```bash
aether profile benchmarks/main.py --max-threads 64
```
Set thread pool size to `optimal_threads` from report.

### Step 4: Verify Environment
```bash
aether status --full
```

### Step 5: Use Adaptive Pool
Replace `ThreadPoolExecutor` with `AdaptiveThreadPool`:

```python
# Before
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=8) as executor:
    results = executor.map(fn, data)

# After
from aether import AdaptiveThreadPool
with AdaptiveThreadPool(max_workers=32) as pool:
    results = pool.map(fn, data)
```

---

## Performance Tips

1. **Use `@atomic` for small critical sections**, not entire functions
2. **Profile before and after** changes to verify improvement
3. **Monitor β (blocking ratio)** in Adaptive Pool to understand your workload
4. **Set thread count to `optimal_threads`** from cliff profiler
5. **Use `ThreadSafeDict` / `ThreadSafeList`** instead of manual locks

---

## Next Steps

- 📖 See [README.md](../README.md) for v0.3.0 feature overview
- 🧪 See [TESTING.md](TESTING.md) for test suite details
- 🔗 See [examples/](../examples/) for more code samples
- 💬 Open an issue for questions or feature requests

