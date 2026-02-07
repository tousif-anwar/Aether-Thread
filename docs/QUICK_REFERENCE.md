# Aether-Thread v0.3.0 Quick Reference

## Installation

```bash
# Basic
pip install aether-thread

# With optional features (recommended)
pip install aether-thread[free-threading]
# or
pip install aether-thread psutil
```

---

## CLI Cheatsheet

### Check Code for Issues
```bash
# Basic check
aether check src/

# With free-threaded Python specific checks
aether check src/ --free-threaded

# Verbose output
aether check src/ --free-threaded --verbose

# Single file
aether check mycode.py
```

### Profile Performance Cliff
```bash
# Default (32 threads)
aether profile benchmark.py

# Custom max threads
aether profile benchmark.py --max-threads 64

# Faster profiling (less accurate)
aether profile benchmark.py --duration 1.0

# Full control
aether profile benchmark.py --max-threads 128 --duration 5.0
```

### Check Environment
```bash
# Quick check
aether status

# Full report
aether status --verbose
```

### Deep Scan
```bash
# All checks
aether scan . --all

# Free-threaded only
aether scan . --free-threaded

# Standard only
aether scan .
```

---

## Python API Cheatsheet

### 1. Detect Thread-Safety Issues

```python
from aether.audit.free_thread_detector import FreeThreadDetector

detector = FreeThreadDetector("mycode.py")
threats = detector.detect(source_code)

for threat in threats:
    print(f"Type: {threat.threat_type.value}")
    print(f"Issue: {threat.description}")
    print(f"Fix: {threat.recommendation}")
    print(f"Crash Risk: {threat.crash_risk}\n")
```

**Threat Types:**
- `frame_locals_access` (🔴 CRASH)
- `warning_catch_context` (🟠 RACE)
- `shared_iterator` (🔴 DATA LOSS)
- `async_threading_mix` (🟠 DEADLOCK)
- `signal_handler_race` (🔴 CRITICAL)
- `exception_group_race` (🟡 CONSISTENCY)

### 2. Profile and Find Cliff

```python
from aether.profile import SaturationCliffProfiler

def workload():
    # Your code here
    do_expensive_work()

profiler = SaturationCliffProfiler(
    workload,
    duration_per_run=5.0,
    max_threads=64
)

analysis = profiler.profile()

print(f"Optimal threads: {analysis.optimal_threads}")
print(f"Cliff at: {analysis.cliff_threads}")
print(f"Severity: {analysis.cliff_severity * 100:.1f}%")
print(analysis.plot_ascii_chart())
```

### 3. Use Adaptive Thread Pool

```python
from aether.pool import AdaptiveThreadPool

# Basic usage
with AdaptiveThreadPool(max_workers=32) as pool:
    results = pool.map(worker_fn, items)

# Check metrics
with AdaptiveThreadPool(max_workers=32) as pool:
    results = pool.map(worker_fn, items)
    
    metrics = pool.get_metrics()
    print(f"Blocking ratio: {metrics.blocking_ratio:.1%}")
    print(f"Active threads: {metrics.active_threads}")
    print(f"Throughput: {metrics.throughput:.0f} ops/sec")
    print(f"Latency: {metrics.avg_latency_ms:.1f}ms")
    
    pool.print_status()

# Submit individual tasks
with AdaptiveThreadPool() as pool:
    future = pool.submit(long_task, arg1, arg2)
    result = future.result()
```

### 4. Check GIL Status

```python
from aether.check import (
    GILStatusChecker,
    get_gil_status,
    is_free_threaded
)

# Quick check
if is_free_threaded():
    print("✅ Free-threaded Python detected")

# Full status
status = get_gil_status()
print(status.value)  # 'enabled', 'disabled', etc

# Detailed report
checker = GILStatusChecker()
status = checker.get_status()
print(f"Python: {status.python_version}")
print(f"Build: {status.build_info}")
print(f"Compatible packages: {status.free_threaded_packages}")
print(f"Potentially unsafe: {status.potentially_unsafe_packages}")

# Print visual report
checker.print_status()
```

---

## Jupyter Notebook Cheatsheet

### Load Extension
```python
%load_ext aether.jupyter_magic
# ✅ Aether magics loaded
```

### Check Cell Code
```python
%%audit [--verbose]
def my_function(shared_dict):
    shared_dict['key'] = value  # Thread-safe?
    return value
```

### Profile Cell Workload
```python
%%profile_threads [--max-threads N] [--duration S]
def workload():
    for i in range(1000):
        expensive_operation()
```

### Check Free-Threading Safety
```python
%%free_threaded_check [--verbose]
import sys
frame = sys._getframe()
local_vars = frame.f_locals  # Safe in free-threaded?
```

### Check Environment
```python
%gil_status [--full]
```

---

## Decision Tree

### "Should I use free-threading now?"
```
├─ Is your code thread-safe? 
│  ├─ Yes → Check with: aether check --free-threaded
│  │         • All 🔴 issues fixed? → Ready
│  │         • Some 🔴 issues? → Fix first
│  │
│  └─ No → Use @atomic decorator or ThreadSafeDict
│
├─ Does it have performance bottlenecks?
│  ├─ Yes → Profile: aether profile benchmark.py
│  │         • Use optimal thread count suggested
│  │
│  └─ No → Single-threaded or use AdaptiveThreadPool
│
└─ Are dependencies compatible?
   ├─ Check: aether status
   │ • All green? → Deploy
   │ • Some warnings? → Review/test
```

---

## Common Patterns

### Pattern 1: Safe Shared State
```python
from aether import atomic, ThreadSafeDict

@atomic
def update_account(account_id, amount):
    accounts[account_id].balance += amount

cache = ThreadSafeDict()
cache[key] = value  # Automatically synchronized
```

### Pattern 2: Find Optimal Thread Count
```python
from aether.profile import SaturationCliffProfiler

analysis = SaturationCliffProfiler(workload).profile()
OPTIMAL_THREADS = analysis.optimal_threads

# Use throughout app
with ThreadPoolExecutor(max_workers=OPTIMAL_THREADS) as executor:
    executor.map(worker, data)
```

### Pattern 3: Adaptive Pool Auto-Tuning
```python
from aether.pool import AdaptiveThreadPool

# Pool auto-scales based on blocking ratio
with AdaptiveThreadPool(max_workers=32) as pool:
    results = pool.map(io_bound_worker, data)
    # If I/O, pool scales up; if CPU, holds steady
```

### Pattern 4: Pre-Deploy Validation
```bash
#!/bin/bash
# pre-deploy.sh

# 1. Check thread-safety
aether check src/ --free-threaded
if [ $? -ne 0 ]; then
    echo "❌ Thread-safety issues found"
    exit 1
fi

# 2. Check environment
aether status --verbose
if [ $? -ne 0 ]; then
    echo "❌ Environment not suitable"
    exit 1
fi

# 3. Profile performance
aether profile production_bench.py

echo "✅ Ready to deploy"
```

---

## Output Interpretation

### `aether check` Output

```
🔴 CRASH RISK (must fix)
  • frame.f_locals access
  • Signal handler with shared state

🟠 SAFETY RISK (should fix)
  • Race condition on shared variable
  • Async + threading mix

🟡 WARNING (review)
  • Potential data race
  • Exception group handling
```

### `aether profile` Output

```
Throughput vs Threads:
  1 ████████████████████ 1000 ops/s
  2 ████████████████████ 1980 ops/s (2x scaling)
  4 ███████████████████░ 3850 ops/s (2x scaling)
  8 ██████░░░░░░░░░░░░░  800 ops/s ← CLIFF

Recommendation: Use 4 threads
```

### `aether status` Output

```
🟢 GIL Status: DISABLED (Free-Threaded!)
Python: 3.13.0
Build: cpython

📦 Compatible: threading, queue, concurrent
⚠️ Caution: numpy, pandas
```

---

## Troubleshooting

### Q: "No module named psutil"
```bash
pip install psutil
# psutil is optional; AdaptiveThreadPool needs it
# Other modules work without it
```

### Q: "ModuleNotFoundError: No module named 'aether'"
```bash
# Make sure installed
pip install aether-thread

# Check installation
python -c "import aether; print(aether.__version__)"
```

### Q: CLI command not found
```bash
# Make sure aether is in PATH
pip install --upgrade aether-thread

# Or use via Python
python -m aether.cli check src/
```

### Q: Jupyter magic not loading
```python
# Make sure installed
import aether.jupyter_magic

# Or force reload
%load_ext aether.jupyter_magic --force
```

---

## Performance Tips

1. **Profile before tuning** – Use SaturationCliffProfiler to find actual cliff
2. **Trust the detector** – Use AutoThreadPool; don't hardcode thread count
3. **Monitor in production** – Check pool metrics periodically
4. **Use @atomic for small sections** – Not entire functions
5. **Batch I/O** – Reduces lock contention

---

## Resources

- 📖 Full guide: [docs/PHASE_3_GUIDE.md](../docs/PHASE_3_GUIDE.md)
- 📋 Delivery summary: [docs/PHASE_3_DELIVERY.md](../docs/PHASE_3_DELIVERY.md)
- 📚 Examples: [examples/](../examples/)
- 🐛 Issues: [GitHub Issues](https://github.com/tousif-anwar/Aether-Thread/issues)

---

## Version Info

```python
import aether
print(aether.__version__)  # 0.3.0
```

**Last Updated:** Phase 3.0-3.2 Complete

