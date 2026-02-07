# Aether-Thread

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)

An open-source **concurrency-optimization toolkit** that helps Python developers transition their legacy code to a thread-safe, **GIL-free environment**.

## The Problem It Solves

For 30 years, Python developers relied on the **Global Interpreter Lock (GIL)** to prevent race conditions at the cost of true parallelism. Now that the GIL can be disabled (in Python 3.13+), many existing libraries will **"break"** or experience **data corruption** because they aren't actually thread-safe.

**Aether-Thread** solves this by providing:
- **Detection tools** to identify non-thread-safe patterns
- **Smart wrappers** that automatically provide synchronization
- **Benchmarking suites** to measure performance improvements

## Core Features

### 🔍 **aether-audit** – Static Analysis
A static analysis tool (built on AST) that scans your codebase and flags non-thread-safe patterns:
- Global mutable variables
- Shared class attributes without synchronization
- Potential data races

```bash
aether-audit src/
```

### 🔒 **aether-proxy** – Smart Thread-Safe Wrappers
Drop-in replacements for standard Python collections with automatic fine-grained locking (only when GIL is disabled):
- `ThreadSafeList` – Thread-safe list wrapper
- `ThreadSafeDict` – Thread-safe dict wrapper
- Dynamically adapts to GIL state

```python
from aether_thread.proxy import ThreadSafeList

safe_list = ThreadSafeList()
safe_list.append(item)  # Automatically synchronized when needed
```

### 📊 **aether-bench** – Benchmarking Suite
Compare performance across:
- Different Python versions
- GIL-on vs GIL-off configurations
- Lock-free vs locking implementations

```bash
aether-bench --all --ops 10000
```

---

## Installation

```bash
pip install aether-thread
```

Or for development:

```bash
git clone https://github.com/tousif-anwar/Aether-Thread.git
cd Aether-Thread
pip install -e .
```

---

## Quick Start

### 1. Audit Your Code

```bash
# Scan a directory for thread-safety issues
aether-audit myproject/

# JSON output for CI/CD integration
aether-audit myproject/ --json --strict
```

**Example output:**
```
AETHER-AUDIT REPORT
====================
Files scanned: 23
Total findings: 8
  - Critical: 5
  - Warnings: 3

Findings:
  🔴 Line 12: [mutable_global]
     Global variable 'cache' is mutable and not synchronized
     💡 Suggestion: Use a thread-safe wrapper or protect access with a Lock
```

### 2. Wrap Unsafe Collections

```python
from aether_thread.proxy import ThreadSafeList, ThreadSafeDict
import threading

# Create thread-safe collections
safe_list = ThreadSafeList()
safe_dict = ThreadSafeDict()

def worker(item_id):
    safe_list.append(item_id)
    safe_dict[f"item_{item_id}"] = item_id * 2

# Spawn multiple threads
threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Safely stored {len(safe_list)} items")
```

### 3. Benchmark Performance

```bash
# Compare threading performance
aether-bench --all --ops 50000

# Focus on specific collections
aether-bench --list --ops 100000
aether-bench --dict --ops 100000
```

---

## Technical Roadmap

| Phase | Goal | Status |
|-------|------|--------|
| **0.1** (Detection) | Build CLI that detects globals and shared attributes | ✅ Complete |
| **0.5** (Mitigation) | Create `@thread_safe` decorator for critical sections | 🚧 In Progress |
| **1.0** (Optimization) | Integrate `sys._is_gil_enabled()` for dynamic switching | 📋 Planned |
| **1.5** (Advanced) | Support async patterns and actor model | 📋 Planned |

---

## Why This Matters

### AI & Data Science
Python is the backbone of AI. Faster, multi-threaded Python means **cheaper and faster training** of models worldwide.

### Legacy Systems
Thousands of companies have **millions of lines of Python code** that need modernization to stay competitive.

### Energy Efficiency
Efficient multi-threading **reduces CPU idle time**, leading to lower energy consumption in massive data centers.

---

## Architecture Overview

```
aether-thread/
├── audit/              # Static analysis engine
│   ├── analyzer.py    # AST-based pattern detection
│   ├── scanner.py     # Directory scanning & reporting
│   └── cli.py         # Command-line interface
├── proxy/             # Thread-safe collections
│   ├── wrapper.py     # Base wrapper with GIL detection
│   ├── collections.py # ThreadSafeList, ThreadSafeDict
│   └── decorators.py  # @thread_safe decorator (coming)
└── bench/             # Performance benchmarking
    ├── benchmarker.py # Core benchmark runner
    ├── runner.py      # Standard benchmark suites
    └── cli.py         # Benchmark CLI
```

---

## Usage Examples

### Detecting Issues

```python
from aether_thread.audit import StaticScanner

scanner = StaticScanner()
results = scanner.scan("src/")
scanner.print_report()
```

### Using Safe Collections in Production

```python
from aether_thread.proxy import ThreadSafeDict
from concurrent.futures import ThreadPoolExecutor

cache = ThreadSafeDict()

def process_item(item_id):
    result = expensive_computation(item_id)
    cache[f"item_{item_id}"] = result
    return result

with ThreadPoolExecutor(max_workers=8) as executor:
    executor.map(process_item, range(1000))

print(f"Processed {len(cache)} items")
```

### Benchmarking

```python
from aether_thread.bench import BenchmarkRunner

runner = BenchmarkRunner()
runner.run_all_benchmarks(num_ops=10000)
```

---

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

Test coverage:
- ✅ AST analysis and pattern detection
- ✅ Directory scanning with exclusions
- ✅ Concurrent list operations
- ✅ Concurrent dict operations
- ✅ GIL state detection

---

## Performance Characteristics

### With GIL Enabled (Python < 3.13 or `PYTHON_GIL=1`)
- **Minimal overhead** – wrappers bypass locking
- **Native GIL protection** – no additional synchronization needed
- **Negligible performance impact**

### With GIL Disabled (Python 3.13+ with `PYTHON_GIL=0`)
- **Fine-grained locking** – automatic mutex acquisition
- **True parallelism** – multiple threads work simultaneously
- **Content-aware** – only synchronizes when needed
- **Performance improvement** – 2-4x speedup on multi-core systems

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

To get started:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Roadmap & Future Work

### Phase 0.5 (Mitigation)
- `@thread_safe` decorator for automatic lock injection
- Support for custom synchronization strategies
- Integration with logging and monitoring

### Phase 1.0 (Optimization)
- Dynamic GIL detection using `sys._is_gil_enabled()`
- Lock-free data structures when GIL is available
- Performance profiling tools

### Phase 1.5+ (Advanced)
- Async/await pattern support
- Actor model implementation
- Distributed lock coordination

---

## Related Resources

- [Python GIL Enhancement Proposal (PEP 703)](https://peps.python.org/pep-0703/)
- [Python 3.13 Release Notes](https://docs.python.org/3.13/whatsnew/3.13.html)
- [Threading Best Practices](https://docs.python.org/3/library/threading.html)
- [Concurrency Patterns](https://realpython.com/intro-to-python-threading/)

---

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## Maintainers

- **Tousif Anwar** – Initial creator and maintainer

---

## Support

- 📖 [Documentation](https://github.com/tousif-anwar/Aether-Thread#readme)
- 🐛 [Issue Tracker](https://github.com/tousif-anwar/Aether-Thread/issues)
- 💬 [Discussions](https://github.com/tousif-anwar/Aether-Thread/discussions)

---

**Made with ❤️ for the Python community**
