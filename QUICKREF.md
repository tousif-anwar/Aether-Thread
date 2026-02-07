# Quick Reference Guide

## Installation

```bash
# Development
cd /workspaces/Aether-Thread
pip install -e .

# Or install from PyPI (when published)
pip install aether-thread
```

---

## Command-Line Tools

### aether-audit – Static Analysis

```bash
# Basic scan
aether-audit src/

# Options
aether-audit src/ --json              # JSON output
aether-audit src/ --strict            # Fail on critical issues
aether-audit src/ --exclude tests     # Exclude directories
aether-audit src/ --verbose -v        # Verbose output
```

**Detects:**
- Mutable global variables
- Shared class attributes
- Unsynchronized modifications

---

### aether-bench – Benchmarking

```bash
# Run all benchmarks
aether-bench --all

# Target specific collections
aether-bench --list --ops 50000
aether-bench --dict --ops 50000

# Options
aether-bench --threads 8  # Number of threads
aether-bench --verbose    # Verbose output
```

---

## Python API

### Static Analysis

```python
from aether_thread.audit import StaticScanner, CodeAnalyzer

# Scan directory
scanner = StaticScanner()
results = scanner.scan('src/')
scanner.print_report()

# Analyze single file
analyzer = CodeAnalyzer("file.py")
result = analyzer.analyze(source_code)
```

### Thread-Safe Collections

```python
from aether_thread.proxy import ThreadSafeList, ThreadSafeDict
import threading

# Safe list
safe_list = ThreadSafeList()
safe_list.append(item)
safe_list.extend([1, 2, 3])

# Safe dict
safe_dict = ThreadSafeDict()
safe_dict['key'] = value
safe_dict.update({...})

# Works with threading
def worker():
    safe_list.append(42)

threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()
```

### Benchmarking

```python
from aether_thread.bench import Benchmarker, BenchmarkRunner

# Standard benchmarks
runner = BenchmarkRunner()
runner.run_all_benchmarks(num_ops=10000)

# Custom benchmark
benchmarker = Benchmarker()
result = benchmarker.run_concurrent_benchmark(
    name="MyTest",
    func=my_function,
    num_threads=4,
    num_operations=10000
)
benchmarker.print_results()
```

---

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_audit.py

# Run with coverage
python -m pytest tests/ --cov=aether_thread

# Verbose output
python -m pytest tests/ -v
```

---

## Common Patterns

### Detecting Issues

```python
from aether_thread.audit import StaticScanner

# Find thread-safety issues in your codebase
scanner = StaticScanner()
results = scanner.scan('myproject/')
scanner.print_report()
```

### Making Code Thread-Safe

```python
from aether_thread.proxy import ThreadSafeList, ThreadSafeDict

# Replace unsafe collections
# OLD: shared_list = []
shared_list = ThreadSafeList()

# OLD: cache = {}
cache = ThreadSafeDict()

# Use normally - synchronization is automatic
shared_list.append(item)
cache[key] = value
```

### Benchmarking Changes

```bash
# Before optimization
aether-bench --all --ops 10000 > before.txt

# After optimization
aether-bench --all --ops 10000 > after.txt

# Compare results
diff before.txt after.txt
```

---

## Project Structure

```
aether_thread/
├── audit/         # Static analysis for thread-safety issues
├── proxy/         # Thread-safe collection wrappers
└── bench/         # Performance benchmarking

tests/             # Unit tests (18+ test cases)
examples/          # Working examples

Documentation:
├── README.md              # Quick start
├── API.md                 # Full API reference
├── CONTRIBUTING.md        # Developer guidelines
├── ROADMAP.md             # Future plans
└── CHANGELOG.md           # Version history
```

---

## Key Classes

### Audit
- `CodeAnalyzer` – AST-based pattern detection
- `StaticScanner` – Directory scanning
- `Finding` – Detected issue
- `ScanResult` – Results from scanning

### Proxy
- `ThreadSafeList` – Thread-safe list
- `ThreadSafeDict` – Thread-safe dict
- `ThreadSafeWrapper` – Base wrapper

### Bench
- `Benchmarker` – Core benchmarking
- `BenchmarkRunner` – Pre-built benchmarks
- `BenchmarkResult` – Benchmark result

---

## Environment Variables

```bash
# Force GIL on (Python 3.13+)
PYTHON_GIL=1 python script.py

# Disable GIL (Python 3.13+)
PYTHON_GIL=0 python script.py
```

---

## Configuration

### pyproject.toml

All configuration uses standard Python conventions in `pyproject.toml`:

```toml
[tool.black]
line-length = 100

[tool.isort]
profile = "black"
```

---

## Performance Tips

1. **Use snapshots for iteration** – ThreadSafeList/Dict create snapshots
2. **Choose appropriate locks** – RLock for reentrant scenarios
3. **Minimize critical sections** – Keep locked code small
4. **Batch operations** – Reduce lock acquisitions

---

## Troubleshooting

### Import errors
```bash
pip install -e .
```

### Tests failing
```bash
python -m pytest tests/ -v
```

### GIL detection
```python
import sys
print("GIL enabled:", sys._is_gil_enabled() if hasattr(sys, '_is_gil_enabled') else "N/A")
```

---

## Resources

- 📖 [README.md](README.md) – Full documentation
- 🔧 [API.md](API.md) – Detailed API reference
- 🎯 [ROADMAP.md](ROADMAP.md) – Future plans
- 👥 [CONTRIBUTING.md](CONTRIBUTING.md) – How to contribute
- 🚀 [examples/demo.py](examples/demo.py) – Working examples

---

**Version**: 0.1.0  
**Python**: 3.9+  
**License**: MIT

