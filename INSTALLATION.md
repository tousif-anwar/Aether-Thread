"""
INSTALLATION AND USAGE GUIDE - Updated for v0.2.0

This document describes how to install and use Aether-Thread with the new
@atomic decorator and contention monitoring features.
"""

# Installation

## Option 1: From PyPI (when published)
```bash
pip install aether-thread
```

## Option 2: Development Installation
```bash
git clone https://github.com/tousif-anwar/Aether-Thread.git
cd Aether-Thread
pip install -e .
```

## Option 3: Direct import (for testing)
```python
import sys
sys.path.insert(0, 'src')
from aether import atomic, ThreadSafeDict
```

---

# Quick Examples

## 1. Using @atomic Decorator

```python
from aether import atomic

class BankAccount:
    def __init__(self):
        self.balance = 0
    
    @atomic
    def deposit(self, amount):
        self.balance += amount
    
    @atomic
    def withdraw(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False

# Use from multiple threads - automatically thread-safe!
account = BankAccount()
```

## 2. Using @synchronized (Simplified)

```python
from aether import synchronized

class Counter:
    def __init__(self):
        self.count = 0
    
    @synchronized
    def increment(self):
        self.count += 1
```

## 3. Thread-Safe Collections

```python
from aether import ThreadSafeDict, ThreadSafeList
import threading

cache = ThreadSafeDict()
results = ThreadSafeList()

def worker():
    cache['key'] = 'value'
    results.append(42)

threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## 4. Contention Monitoring

```python
from aether import atomic
from aether.monitor import get_monitor

monitor = get_monitor()
monitor.enable()

class MyService:
    @atomic
    def operation(self):
        pass

# ... run your code ...

stats = monitor.get_stats()
hot_locks = stats.get_hot_locks(threshold=20.0)
monitor.print_report()
```

---

# Decorator Parameters

## @atomic

```python
@atomic(
    lock_type=LockType.RLOCK,           # Type of lock
    strategy=SynchronizationStrategy.ADAPTIVE,  # When to lock
    timeout=None,                       # Lock acquisition timeout
    track_contention=False              # Enable monitoring
)
def my_method(self):
    pass
```

### Lock Types
- `LockType.LOCK` – Basic mutual exclusion
- `LockType.RLOCK` – Reentrant (can be called from itself)
- `LockType.SEMAPHORE` – Resource limiting

### Strategies
- `ADAPTIVE` – Always lock for safety (default)
- `GIL_DISABLED` – Only lock when GIL is disabled
- `ALWAYS` – Always lock, regardless

## @synchronized

```python
@synchronized(timeout=None)  # Simple version with sensible defaults
def my_method(self):
    pass
```

---

# Project Structure (v0.2.0)

```
src/aether/
├── __init__.py              # Main package
├── decorators.py            # @atomic, @synchronized
├── monitor.py               # ContentionMonitor
├── collections/
│   └── __init__.py          # ThreadSafeList/Dict/Set
├── audit/
│   ├── __init__.py
│   ├── analyzer.py
│   └── scanner.py
└── benchmark/
    ├── __init__.py
    ├── benchmarker.py
    └── runner.py
```

---

# Summary of Changes (0.1.0 → 0.2.0)

| Feature | Added | Description |
|---------|-------|-------------|
| `@atomic` | ✅ | Method-level synchronization with options |
| `@synchronized` | ✅ | Simplified version of @atomic |
| ContentionMonitor | ✅ | Real-time lock contention tracking |
| ThreadSafeSet | ✅ | Added to collections |
| src/ structure | ✅ | Professional package organization |
| Tests | +18 | New decorator and monitor tests |
| Examples | +1 | bank_account.py showcase |

---

# Testing

```bash
# All tests
export PYTHONPATH=src
python -m unittest discover tests/

# Specific test file
python -m unittest tests.test_decorators

# Single test class
python -m unittest tests.test_decorators.TestAtomicDecorator
```

---

# Troubleshooting

### Issue: Import errors with `src/aether`

**Solution:** Make sure `src/` is in your PYTHONPATH:
```bash
export PYTHONPATH=/path/to/project/src
python your_script.py
```

Or use:
```python
import sys
sys.path.insert(0, 'src')
from aether import atomic
```

### Issue: Tests fail with "No module named 'aether'"

**Solution:** Set PYTHONPATH before running tests:
```bash
export PYTHONPATH=src
python -m unittest discover
```

---

# Performance Notes

### With GIL Enabled
- Overhead: ~5% – Decorator bypasses locking
- Benefit: No performance penalty

### With GIL Disabled (Python 3.13+)
- Overhead: 15-30% – Fine-grained locking
- Benefit: True multi-core parallelism (2-8x faster)

---

# Next Steps

1. Read [README.md](README.md) for full feature overview
2. Check [API.md](API.md) for detailed reference
3. Run examples in `examples/` directory
4. Explore [ROADMAP.md](ROADMAP.md) for upcoming features

