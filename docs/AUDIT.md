# aether-audit: Static Analysis for Thread-Safety

> Detect thread-safety issues before they cause crashes in production.

**aether-audit** is a comprehensive static analysis toolkit that helps Python developers identify and fix concurrency bugs. It uses Abstract Syntax Tree (AST) analysis to find three critical categories of thread-safety issues:

1. **Shared Mutable State** - Global variables, class attributes, mutable defaults
2. **Race Condition Patterns** - Check-then-act, read-modify-write, compound operations  
3. **Auto-Lock Suggestions** - Automated recommendations for adding synchronization

## Why It Matters

In Python 3.13+ with the GIL removed, all multi-threaded code becomes potentially dangerous. A single shared mutable variable accessed from two threads simultaneously can cause:

- 🔴 **Silent data corruption** - Your program runs but produces wrong answers
- 🟡 **Non-deterministic crashes** - Failures only happen under high load
- 🟠 **Production incidents** - Bugs that evaded testing and review

**aether-audit** finds these bugs *before* they reach production by analyzing your code statically, without needing to run it.

## Quick Start

### Single File Audit

```python
from aether.audit import audit_code

code = """
counter = 0  # Mutable global!

def increment():
    global counter
    counter += 1  # RACE CONDITION - not atomic
"""

report = audit_code(code, "myfile.py")
print(report)
```

Output:
```
════════════════════════════════════════════════════════════════════════════════
AETHER-AUDIT REPORT: myfile.py
════════════════════════════════════════════════════════════════════════════════

🔴 SHARED STATE ISSUES (1 found):
────────────────────────────────────────────────────────────────────────────────
  Line 1: Global variable 'counter' is mutable and accessible from multiple threads
  → Fix: Use @atomic decorator on functions that modify 'counter', or wrap with ThreadSafe wrapper

🟡 RACE CONDITIONS (2 patterns found):
────────────────────────────────────────────────────────────────────────────────
  Line 6: Compound assignment 'counter += ...' is not atomic
  → Fix: Use @atomic decorator on function containing 'counter += ...'

════════════════════════════════════════════════════════════════════════════════
SUMMARY:
  Mutable Globals: 1
  Mutable Class Attributes: 0  
  Race Conditions: 2
  Total Issues: 3
════════════════════════════════════════════════════════════════════════════════
```

### Directory Audit

```python
from aether.audit import audit_directory

# Audit entire project
report = audit_directory("/path/to/myproject")
print(report)
```

## Three Detection Systems

### 1. 🔴 Shared State Detector

Finds mutable global variables, shared class attributes, and problematic default arguments.

#### Detects:

**Global Mutable Variables**
```python
counter = 0  # ❌ Multiple threads can access/modify
items = []   # ❌ Shared across threads
cache = {}   # ❌ Concurrent modifications conflict
```

**Class-Level Shared State**
```python
class MyClass:
    cache = {}        # ❌ Shared by ALL instances!
    shared_list = []  # ❌ Every MyClass() shares this
```

**Mutable Default Arguments**
```python
def process(items=[]):  # ❌ [] created ONCE at definition
    items.append(1)
    return items

# Call 1: [1]          # [] is empty when called
# Call 2: [1, 2]       # [] was NEVER recreated!
# Under threading: Same [] accessed by multiple threads = RACE CONDITION
```

#### Fixes:

```python
# ✅ Global: Use @atomic decorator
from aether import atomic

@atomic
def increment():
    global counter
    counter += 1

# ✅ Global: Use ThreadSafe wrapper
from aether import ThreadSafeList, ThreadSafeDict

items = ThreadSafeList()      # Automatically synchronized
cache = ThreadSafeDict()      # Automatically synchronized

# ✅ Class attribute: Move to __init__
class MyClass:
    def __init__(self):
        self.cache = {}        # Each instance has its own copy
        self.shared_list = []
        
# ✅ Mutable defaults: Use None
def process(items=None):
    if items is None:
        items = []             # Fresh list each call
    items.append(1)
    return items
```

### 2. 🟡 Race Condition Simulator

Detects common concurrency patterns that cause non-deterministic failures.

#### Pattern 1: Compound Operations

```python
# ❌ NOT atomic - potential race condition
counter += 1

# Under the hood, Python does THREE separate operations:
# 1. READ counter (value = 5)
# 2. ADD 1 (5 + 1 = 6)  
# 3. WRITE back (counter = 6)
#
# Thread A: READ (5)
# Thread B: READ (5) - doesn't see A's write yet!
# Thread A: WRITE (6)
# Thread B: WRITE (6) - overwrites A's increment!
# Result: counter = 6, but should be 7!
```

#### Pattern 2: Check-Then-Act (TOCTOU)

```python
# ❌ RACE WINDOW between check and action
if balance > 100:        # Check at T1
    balance -= 100       # Act at T2 + 500ms
    
# Thread A: Check (balance = 150) ✓ Passes
#   [500ms delay, network call, etc.]
# Thread B: Check (balance = 150) ✓ Also passes!
# Thread B: withdraws 100 (balance = 50)
# Thread A: withdraws 100 (balance = -50) ❌ OVERDRAFT!
```

#### Pattern 3: Read-Modify-Write

```python
# ❌ NOT atomic
total = total + new_amount

# Breaks down to: READ total, ADD new_amount, WRITE back
# Same race condition as compound operations
```

#### Fixes:

```python
from aether import atomic

# ✅ Solution 1: @atomic decorator (recommended)
@atomic
def increment():
    global counter
    counter += 1

b# ✅ Solution 2: Explicit lock
import threading

balance_lock = threading.RLock()

def withdraw(amount):
    with balance_lock:
        if balance > amount:
            balance -= amount
            return True
    return False

# ✅ Solution 3: ThreadSafe wrapper
from aether import ThreadSafeDict

accounts = ThreadSafeDict()
# All operations automatically synchronized!
```

### 3. 🟢 Auto-Lock Injector

Suggests three strategies for adding synchronization, in order of ease:

#### Strategy 1: @atomic Decorator (Easiest)

```python
from aether import atomic

@atomic
def transfer(from_account, to_account, amount):
    from_account.balance -= amount
    to_account.balance += amount
    # All operations execute without interference
```

**Pros:**
- Simplest to add (one line)
- Minimum overhead
- Clear intent

**Cons:**
- Locks entire function
- Can't have partial coverage

#### Strategy 2: ThreadSafe Collections (Best for Shared Data)

```python
from aether import ThreadSafeDict, ThreadSafeList

# Instead of:
# cache = {}
# 
# Use:
cache = ThreadSafeDict()

# Every operation is automatically protected:
cache['key'] = value        # Thread-safe
value = cache['key']        # Thread-safe
del cache['key']            # Thread-safe
cache.update(other_dict)    # Thread-safe
```

**Pros:**
- Automatic protection for common operations
- Fine-grained locking (per-operation)
- Familiar API (use like normal dict/list)

**Cons:**
- Only helps for collections
- Multiple operations might need @atomic

#### Strategy 3: Explicit Locks (Most Control)

```python
import threading

global_state_lock = threading.RLock()

def critical_section():
    with global_state_lock:
        # Multiple operations protected
        var1 = read_state()
        result = process(var1)
        write_state(result)
        # Lock released when exiting with block
```

**Pros:**
- Fine-grained control
- Multiple operations in one critical section
- Can be used anywhere (not just methods)

**Cons:**
- More verbose
- Easy to forget lock somewhere
- Potential deadlock if nested

## Detection Severity Levels

| Severity | Issue | Example |
|----------|-------|---------|
| 🔴 CRITICAL | Mutable global variable | `items = []` at module level |
| 🔴 CRITICAL | Mutable class attribute | `class X: cache = {}` |
| 🟡 WARNING | Mutable default argument | `def f(x=[])` |
| 🟡 WARNING | Race condition pattern | `counter += 1` without sync |
| 🔵 INFO | Unsynchronized access | Multiple reads/writes to same var |

## API Reference

### Main Functions

#### `audit_code(source_code: str, filename: str = "unknown.py") -> str`

Quick audit of Python source code.

```python
from aether.audit import audit_code

code = open("myfile.py").read()
report = audit_code(code, "myfile.py")
print(report)
```

#### `audit_directory(directory_path: str, exclude_dirs: List[str] = None) -> str`

Recursively audit all Python files in a directory.

```python
from aether.audit import audit_directory

report = audit_directory(
    "/path/to/project",
    exclude_dirs=["venv", "node_modules", ".git"]
)
print(report)
```

### Classes

#### `CodeAnalyzer`

Low-level API for analyzing individual files.

```python
from aether.audit import CodeAnalyzer

analyzer = CodeAnalyzer("myfile.py")
result = analyzer.analyze(source_code)

print(f"Mutable globals: {result.mutable_globals}")
print(f"Findings: {len(result.findings)}")

for finding in result.findings:
    print(f"{finding.severity}: {finding.description}")
    print(f"  Location: {finding.file_path}:{finding.line_number}")
    print(f"  Fix: {finding.suggestion}")
```

#### `RaceConditionDetector`

Detects concurrent access patterns.

```python
from aether.audit import RaceConditionDetector, RacePattern

detector = RaceConditionDetector("myfile.py")
races = detector.detect(source_code)

for race in races:
    if race.pattern_type == RacePattern.CHECK_THEN_ACT.value:
        print(f"⚠️  Check-then-act on {race.affected_variable}")
    print(f"  Lines: {race.line_numbers}")
    print(f"  Fix: {race.fix_suggestion}")
```

#### `AutoLockInjector`  

Generates synchronization suggestions.

```python
from aether.audit import AutoLockInjector

injector = AutoLockInjector("myfile.py", source_code)

# Suggest fixes for mutable global
suggestions = injector.analyze_mutable_global('counter', line=10, var_type='int')

for sugg in suggestions:
    print(f"{sugg.suggestion_type.upper()}")
    print(f"  Target: {sugg.target_name}")
    print(f"  Current: {sugg.current_code}")
    print(f"  Fixed: {sugg.suggested_code}")
```

## Common Issues and Fixes

### Issue #1: Global Counter

```python
# ❌ BAD
requests_handled = 0

def handle_request():
    global requests_handled
    requests_handled += 1
    process_request()

# ✅ FIX 1: Use @atomic
from aether import atomic

@atomic
def handle_request():
    global requests_handled
    requests_handled += 1
    process_request()

# ✅ FIX 2: Use explicit lock
import threading
requests_lock = threading.Lock()

def handle_request():
    global requests_handled
    with requests_lock:
        requests_handled += 1
    process_request()
```

### Issue #2: Shared Cache

```python
# ❌ BAD
class UserManager:
    user_cache = {}  # Shared by ALL instances!
    
    def get_user(self, user_id):
        if user_id not in self.user_cache:
            self.user_cache[user_id] = fetch_from_db(user_id)
        return self.user_cache[user_id]

# ✅ FIX 1: Move to __init__
class UserManager:
    def __init__(self):
        self.user_cache = {}  # Each instance has own cache
    
    def get_user(self, user_id):
        if user_id not in self.user_cache:
            self.user_cache[user_id] = fetch_from_db(user_id)
        return self.user_cache[user_id]

# ✅ FIX 2: Use ThreadSafeDict
from aether import ThreadSafeDict

class UserManager:
    user_cache = ThreadSafeDict()  # Thread-safe shared cache
    
    def get_user(self, user_id):
        if user_id not in self.user_cache:
            self.user_cache[user_id] = fetch_from_db(user_id)
        return self.user_cache[user_id]
```

### Issue #3: Mutable Default

```python
# ❌ BAD - shared list across calls
def add_user(user, users=[]):
    users.append(user)
    return users

add_user("Alice")         # ["Alice"]
add_user("Bob")           # ["Alice", "Bob"] - where did Alice come from?!

# ✅ FIX
def add_user(user, users=None):
    if users is None:
        users = []  # Fresh list each call
    users.append(user)
    return users
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Thread Safety Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Aether
        run: pip install aether-thread
      
      - name: Audit codebase
        run: |
          python -c "
          from aether.audit import audit_directory
          report = audit_directory('src')
          print(report)
          
          # Fail if critical issues found
          if '🔴 CRITICAL' in report:
              exit(1)
          "
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: aether-audit
        name: Aether Thread-Safety Audit
        entry: python -c "from aether.audit import audit_directory; print(audit_directory('.'))"
        language: system
        types: [python]
        stages: [commit]
```

## Limitations and Caveats

Current limitations:

1. **Static analysis only** - Cannot detect all race conditions (some require runtime)
2. **False positives** - May flag safe code as unsafe (better safe than sorry)  
3. **Python 3.9+** - Uses ast module features from Python 3.9+
4. **No type checking** - Doesn't verify types, may miss some issues
5. **No data flow** - Doesn't track how variables flow through code

What this tool does NOT do:

- ❌ Detect deadlocks (requires runtime analysis)
- ❌ Find all data races (would require full program analysis)
- ❌ Optimize lock placement (focus is on detection)
- ❌ Handle distributed locking (local threading only)

## Best Practices

1. **Run regularly** - Add to CI/CD pipeline to catch regressions
2. **Review carefully** - Read all findings, some may be false positives
3. **Use decorator-first** - @atomic is easiest to get right
4. **Test concurrent scenarios** - Static analysis + runtime testing
5. **Document assumptions** - Mark when shared state is intentional

## Examples

See `/examples/audit_demo.py` for comprehensive examples:

```bash
python examples/audit_demo.py
```

This runs four detailed demonstrations:

1. Detects unsafe code with globals and race conditions
2. Shows fixed version with proper synchronization
3. Explains class-level shared state pitfalls
4. Demonstrates mutable default argument dangers

## Contributing

Issues, suggestions, and contributions welcome! The audit system is designed to be extensible - add new detection patterns by subclassing the AST visitors.

## See Also

- [aether.audit.CodeAnalyzer](analyzer.py) - Shared state detection
- [aether.audit.RaceConditionDetector](race_detector.py) - Race pattern detection
- [aether.audit.AutoLockInjector](lock_injector.py) - Fix suggestions
- [aether-thread documentation](../README.md) - Full toolkit
- [Python AST docs](https://docs.python.org/3/library/ast.html) - How this works
