# Aether-Thread 🧵

An open-source concurrency-optimization toolkit that helps Python developers transition their legacy code to a thread-safe, GIL-free environment.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Aether-Thread is a comprehensive toolkit designed to help Python developers prepare their code for Python 3.13+ GIL-free mode and multi-threaded environments. It provides:

- 🔍 **Thread-Safety Analysis**: Detect GIL-dependent patterns and potential race conditions
- 🔧 **Code Transformation**: Automatically add thread-safety mechanisms to legacy code
- 📊 **Performance Profiling**: Measure GIL contention and threading efficiency
- 🛡️ **Thread-Safe Utilities**: Ready-to-use decorators and data structures

## Features

### 1. Thread-Safety Analyzer

Analyze your Python code to identify thread-safety issues:

```python
from aether_thread import ThreadSafetyAnalyzer

analyzer = ThreadSafetyAnalyzer()
issues = analyzer.analyze_code(your_code)

for issue in issues:
    print(f"[{issue.severity}] {issue.message}")
```

### 2. Thread-Safe Decorators

Make your functions thread-safe with simple decorators:

```python
from aether_thread import thread_safe, gil_free_compatible

@thread_safe
def increment_counter():
    global counter
    counter += 1

@gil_free_compatible(strict=True)
def safe_computation(data):
    return sum(data)
```

### 3. GIL Contention Profiler

Profile your multi-threaded code to identify bottlenecks:

```python
from aether_thread import GILContentionProfiler

profiler = GILContentionProfiler()
profiler.start()

# Your multi-threaded code here

profiler.stop()
profiler.print_report()
```

### 4. Thread-Safe Data Structures

Use built-in thread-safe data structures:

```python
from aether_thread.decorators import ThreadSafeCounter, ThreadSafeDict

counter = ThreadSafeCounter(0)
counter.increment()

cache = ThreadSafeDict()
cache.set('key', 'value')
```

## Installation

### From Source

```bash
git clone https://github.com/tousif-anwar/Aether-Thread.git
cd Aether-Thread
pip install -e .
```

### Using pip (once published)

```bash
pip install aether-thread
```

## Quick Start

### Command-Line Interface

Aether-Thread provides a powerful CLI for analyzing and transforming your code:

```bash
# Analyze a Python file for thread-safety issues
aether-thread analyze mycode.py

# Get detailed suggestions
aether-thread analyze mycode.py --verbose

# Transform code to add thread-safety
aether-thread transform mycode.py --dry-run

# Apply transformations
aether-thread transform mycode.py -o safe_mycode.py

# Get improvement suggestions
aether-thread suggest mycode.py
```

### Python API

```python
from aether_thread import ThreadSafetyAnalyzer

# Analyze code
analyzer = ThreadSafetyAnalyzer()
code = """
global counter
counter = 0

def increment():
    global counter
    counter += 1
"""

issues = analyzer.analyze_code(code)
summary = analyzer.get_summary()

print(f"Thread-safe: {summary['is_thread_safe']}")
print(f"Issues found: {summary['total_issues']}")
```

## Examples

Check out the `examples/` directory for complete examples:

- `basic_usage.py`: Demonstrates all major features
- `legacy_code.py`: Example of code that needs thread-safety improvements

Run the examples:

```bash
python examples/basic_usage.py
```

## Use Cases

### Migrating to Python 3.13+ GIL-Free Mode

Python 3.13+ introduces experimental GIL-free mode. Aether-Thread helps you:

1. Identify code that relies on GIL protection
2. Add explicit synchronization where needed
3. Measure the performance impact of changes
4. Validate thread-safety of your code

### Improving Multi-Threaded Applications

Even in standard Python, Aether-Thread helps:

- Find race conditions before they cause bugs
- Add proper locking mechanisms
- Profile and optimize thread performance
- Migrate from threading to multiprocessing where beneficial

## Architecture

Aether-Thread consists of four main components:

1. **Analyzer** (`analyzer.py`): AST-based code analysis for thread-safety
2. **Decorators** (`decorators.py`): Thread-safe decorators and data structures
3. **Profiler** (`profiler.py`): Performance profiling for concurrent code
4. **Transformer** (`transformer.py`): Automatic code transformation utilities

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=aether_thread --cov-report=html
```

### Code Style

```bash
# Format code
black aether_thread/ tests/

# Type checking
mypy aether_thread/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] Support for more complex thread-safety patterns
- [ ] Integration with popular Python frameworks (Django, Flask, FastAPI)
- [ ] Visual profiling reports and graphs
- [ ] IDE plugins (VSCode, PyCharm)
- [ ] Automated fix suggestions with ML
- [ ] Support for async/await patterns

## Resources

- [Python 3.13 GIL-free mode documentation](https://docs.python.org/3.13/)
- [Threading best practices](https://docs.python.org/3/library/threading.html)
- [Multiprocessing module](https://docs.python.org/3/library/multiprocessing.html)

## Acknowledgments

Special thanks to the Python community and all contributors working on making Python more concurrent and performant.

## Contact

Tousif Anwar - [@tousif-anwar](https://github.com/tousif-anwar)

Project Link: [https://github.com/tousif-anwar/Aether-Thread](https://github.com/tousif-anwar/Aether-Thread)
