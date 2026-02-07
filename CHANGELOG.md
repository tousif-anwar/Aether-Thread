# Changelog

All notable changes to this project are documented in this file.

## [0.2.0] – 2026-02-07 (Phase 0.5 – Synchronization)

### ✨ Major Features

**Added:**
- ✅ `@atomic` decorator – Automatic thread-safe method synchronization
  - Flexible lock type configuration (LOCK, RLOCK, SEMAPHORE)
  - GIL-aware behavior (minimal overhead when GIL enabled)
  - Reentrant locking support
  - Optional timeout on lock acquisition
- ✅ `@synchronized` decorator – Simplified thread-safety for common cases
  - Sensible defaults for standard use cases
  - Drop-in replacement for manual locking
- ✅ Contention monitoring system
  - Real-time lock contention tracking
  - Identifies "hot locks" causing bottlenecks
  - Automatic performance suggestions
  - Detailed diagnostic reports
- ✅ Professional `src/aether/` package structure
- ✅ ThreadSafeSet collection (added to collections)
- ✅ Comprehensive examples with BankAccount demo

### 🏗️ Architecture Changes

**Restructured to professional Python package layout:**
```
aether_thread/     → src/aether/
├── decorators.py    (NEW)
├── monitor.py       (NEW)
├── collections/
├── audit/
└── benchmark/
```

**Benefits:**
- Follows PEP 517/518 modern Python packaging standards
- Better IDE support and type checking
- Cleaner namespace management
- Industry-standard structure

### 📊 New Metrics & Monitoring

- **ContentionMonitor** – Singleton that tracks all locks
- **ContentionMetrics** – Per-lock statistics (acquisitions, wait times, contention rate)
- **ContentionLevel** – Automatic severity classification
- **ContentionStats** – Aggregate reporting and analysis

### 🧪 Testing Enhancements

**New test modules:**
- `test_decorators.py` – 15+ tests for @atomic and @synchronized
- `test_monitor.py` – 10+ tests for contention monitoring
- Concurrent thread-safety verification tests
- Exception handling and reentrant locking tests

### 📝 Documentation

**Updated/Added:**
- Complete README with @atomic examples
- API.md with decorator and monitor docs
- bank_account.py example (BankAccount + transfers + monitoring)
- QUICKREF.md for quick lookup

### 🔄 Backward Compatibility

- ✅ Original aether_thread package still available for imports
- ✅ All 0.1.0 functionality preserved
- Thread-safe collections work exactly as before

---

## [0.1.0] – 2026-02-07 (Phase 0.1 – Detection)

### Initial Release

**Added:**
- ✅ **aether-audit** – Static analysis for thread-safety issues
  - AST-based detection engine
  - Global variable scanning
  - Class attribute analysis
  - CLI interface with JSON output
- ✅ **aether-proxy** – Thread-safe collections
  - ThreadSafeList wrapper
  - ThreadSafeDict wrapper
  - Automatic fine-grained locking
  - GIL-aware behavior
- ✅ **aether-bench** – Benchmarking suite
  - Concurrent benchmarks
  - Sequential baselines
  - GIL state detection
- ✅ Comprehensive test suite (18+ tests)
- ✅ Full documentation and examples

---

## Planned Releases

### [0.5.0] – Q2 2026 (Phase 0.5 Enhancement)

**Planned but not yet implemented:**
- Lock-free data structures when GIL is available
- Performance profiling integration
- Custom synchronization strategies
- Enhanced static analysis patterns

### [1.0.0] – Q3 2026 (Phase 1.0 – Optimization)

**Planned:**
- `sys._is_gil_enabled()` integration
- Dynamic lock/lock-free switching
- Advanced performance optimizations
- Distributed locking support

### [1.5.0] – Q4 2026+ (Phase 1.5 – Advanced)

**Planned:**
- Async/await pattern support
- Actor model implementation
- Advanced concurrency patterns
- Web dashboard for monitoring

---

## Version History

| Version | Release | Status | Focus |
|---------|---------|--------|-------|
| 0.1.0 | Feb 2026 | ✅ Complete | Detection & Analysis |
| 0.2.0 | Feb 2026 | ✅ Complete | Synchronization Decorators |
| 0.5.0+ | Q2+ 2026 | 📋 Planned | Optimization & Advanced |

---

## Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):
- **Major** (0.x) – Significant feature releases or breaking changes
- **Minor** (x.y) – New features, backward compatible
- **Patch** (x.y.z) – Bug fixes and patches

---

