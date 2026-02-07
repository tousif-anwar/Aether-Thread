# API Documentation

## Aether-Audit

### `CodeAnalyzer`

Static analyzer for detecting thread-safety issues using AST.

```python
from aether_thread.audit import CodeAnalyzer

analyzer = CodeAnalyzer(filename="path/to/file.py")
result = analyzer.analyze(source_code)
```

#### Methods

- **`analyze(source_code: str) -> ScanResult`**
  - Parse and analyze Python source code
  - Returns: ScanResult with findings and details

#### Attributes

- **`findings: List[Finding]`** – List of detected issues
- **`global_variables: List[str]`** – Global variables found
- **`class_attributes: Dict[str, List[str]]`** – Class attributes by class

---

### `StaticScanner`

Recursively scans directories for thread-safety issues.

```python
from aether_thread.audit import StaticScanner

scanner = StaticScanner(exclude_dirs=['.venv', 'node_modules'])
results = scanner.scan('src/')
scanner.print_report()
```

#### Methods

- **`scan(root_path: str) -> Dict[str, ScanResult]`**
  - Recursively scan a directory
  - Returns: Dictionary mapping file paths to scan results

- **`get_summary() -> Dict[str, Any]`**
  - Get summary statistics
  - Returns: Summary with counts by severity

- **`print_report() -> None`**
  - Print formatted report to console

#### Attributes

- **`results: Dict[str, ScanResult]`** – Results per file
- **`total_findings: List[Finding]`** – All findings across files

---

### `Finding`

Represents a detected thread-safety issue.

```python
@dataclass
class Finding:
    line_number: int
    file_path: str
    issue_type: str  # "mutable_global", "mutable_class_attribute", etc.
    description: str
    severity: str    # "critical", "warning", "info"
    code_snippet: str
    suggestion: Optional[str] = None
```

---

### `ScanResult`

Results from analyzing a single file.

```python
@dataclass
class ScanResult:
    file_path: str
    findings: List[Finding]
    global_variables: List[str]
    class_attributes: List[str]
```

---

### CLI: `aether-audit`

Command-line interface for static analysis.

```bash
aether-audit [PATH] [OPTIONS]

Options:
  --exclude DIR1 DIR2    Directories to exclude
  --json                 Output as JSON
  --strict               Exit with error if critical issues found
  -v, --verbose          Verbose output
```

#### Examples

```bash
# Scan current directory
aether-audit

# Scan specific directory
aether-audit src/

# JSON output
aether-audit src/ --json

# Strict mode for CI/CD
aether-audit src/ --strict --exclude tests venv
```

---

## Aether-Proxy

### `ThreadSafeList`

Thread-safe wrapper for Python lists with automatic synchronization.

```python
from aether_thread.proxy import ThreadSafeList

lst = ThreadSafeList()
lst.append(item)
```

#### Methods

- **`append(item: Any) -> None`** – Add item to end
- **`extend(items: List) -> None`** – Add multiple items
- **`insert(index: int, item: Any) -> None`** – Insert at position
- **`remove(item: Any) -> None`** – Remove first occurrence
- **`pop(index: int = -1) -> Any`** – Remove and return item
- **`clear() -> None`** – Remove all items

#### Special Methods

- **`__len__() -> int`** – Get list length
- **`__getitem__(index) -> Any`** – Access item by index
- **`__setitem__(index, value) -> None`** – Set item by index
- **`__contains__(item) -> bool`** – Check membership
- **`__iter__() -> Iterator`** – Iterate over items (snapshot)

---

### `ThreadSafeDict`

Thread-safe wrapper for Python dicts with automatic synchronization.

```python
from aether_thread.proxy import ThreadSafeDict

d = ThreadSafeDict()
d['key'] = 'value'
```

#### Methods

- **`get(key: Any, default: Any = None) -> Any`** – Get with default
- **`pop(key: Any, *args) -> Any`** – Remove and return value
- **`update(other: Dict) -> None`** – Update from another dict
- **`clear() -> None`** – Remove all items

#### Special Methods

- **`__setitem__(key, value) -> None`** – Set item
- **`__getitem__(key) -> Any`** – Get item
- **`__delitem__(key) -> None`** – Delete item
- **`__len__() -> int`** – Get dict size
- **`__contains__(key) -> bool`** – Check if key exists
- **`__iter__() -> Iterator`** – Iterate over keys (snapshot)

#### Methods

- **`keys() -> List`** – Get all keys (snapshot)
- **`values() -> List`** – Get all values (snapshot)
- **`items() -> List`** – Get all items (snapshot)

#### Behavior

- **GIL Enabled**: Minimal overhead, bypasses locking
- **GIL Disabled**: Automatic fine-grained locking with RLock

---

### `ThreadSafeWrapper`

Base class for custom thread-safe wrappers.

```python
from aether_thread.proxy import ThreadSafeWrapper

class MyThreadSafeClass(ThreadSafeWrapper):
    def my_method(self):
        return self._with_lock(lambda: self._object.operation())
```

#### Methods

- **`_with_lock(func: Callable) -> Any`** – Execute function with lock if needed
- **`_is_gil_disabled() -> bool`** – Static method to check GIL state

---

## Aether-Bench

### `Benchmarker`

Core benchmarking engine.

```python
from aether_thread.bench import Benchmarker

benchmarker = Benchmarker()
result = benchmarker.run_concurrent_benchmark(
    name="MyBenchmark",
    func=my_function,
    num_threads=4,
    num_operations=10000
)
```

#### Methods

- **`run_sequential_benchmark(name: str, func: Callable, num_operations: int) -> BenchmarkResult`**
  - Run single-threaded benchmark

- **`run_concurrent_benchmark(name: str, func: Callable, num_threads: int, num_operations: int) -> BenchmarkResult`**
  - Run multi-threaded benchmark

- **`get_results() -> List[BenchmarkResult]`**
  - Get all results

- **`print_results() -> None`**
  - Print formatted results table

#### Properties

- **`python_version: str`** – Python version being used
- **`results: List[BenchmarkResult]`** – All benchmark results

---

### `BenchmarkResult`

Results from a single benchmark run.

```python
@dataclass
class BenchmarkResult:
    name: str
    total_time: float
    operations: int
    ops_per_second: float
    threads: int
    gil_enabled: bool
    python_version: str
    details: Dict[str, Any] = field(default_factory=dict)
```

---

### `BenchmarkRunner`

Pre-configured benchmarks for common patterns.

```python
from aether_thread.bench import BenchmarkRunner

runner = BenchmarkRunner()
runner.run_list_benchmarks(num_ops=10000)
runner.benchmarker.print_results()
```

#### Methods

- **`run_list_benchmarks(num_ops: int = 10000) -> List[BenchmarkResult]`**
  - Benchmark list operations

- **`run_dict_benchmarks(num_ops: int = 10000) -> List[BenchmarkResult]`**
  - Benchmark dict operations

- **`run_all_benchmarks(num_ops: int = 10000) -> None`**
  - Run and display all benchmarks

---

### CLI: `aether-bench`

Command-line interface for benchmarking.

```bash
aether-bench [OPTIONS]

Options:
  --all              Run all benchmarks
  --list             Run list benchmarks
  --dict             Run dict benchmarks
  --ops N            Number of operations (default: 10000)
  --threads N        Number of threads (default: 4)
  -v, --verbose      Verbose output
```

#### Examples

```bash
# Run all benchmarks
aether-bench --all

# List benchmarks with 50k operations
aether-bench --list --ops 50000

# Dict benchmarks with 8 threads
aether-bench --dict --threads 8
```

---

## Version Information

- **Current Version**: 0.1.0
- **Python Support**: 3.9 - 3.13+
- **Status**: Alpha (Breaking changes possible)

---

## Performance Notes

### Thread-Safe Collections Overhead

When **GIL is enabled** (Python < 3.13):
- **Overhead**: < 5% for most operations
- **Reason**: Lock acquisition bypassed, GIL provides safety

When **GIL is disabled** (Python 3.13+):
- **Overhead**: 15-30% for fine-grained locking
- **Benefit**: Enables true parallelism with safety

### Snapshots for Iteration

Both ThreadSafeList and ThreadSafeDict use **snapshots** when iterating:
- Prevents concurrent modification errors
- Slight memory overhead for large collections
- Ensures consistent iteration

---

## Best Practices

### Safe Threading

```python
from aether_thread.proxy import ThreadSafeDict
from concurrent.futures import ThreadPoolExecutor

shared_data = ThreadSafeDict()

def worker(item_id):
    result = expensive_operation(item_id)
    shared_data[item_id] = result

with ThreadPoolExecutor(max_workers=8) as executor:
    executor.map(worker, range(100))
```

### Audit Before Migration

```python
from aether_thread.audit import StaticScanner

scanner = StaticScanner()
results = scanner.scan('legacy_codebase/')
scanner.print_report()
```

### Benchmark Changes

```python
from aether_thread.bench import BenchmarkRunner

runner = BenchmarkRunner()
runner.run_all_benchmarks(num_ops=50000)
```

