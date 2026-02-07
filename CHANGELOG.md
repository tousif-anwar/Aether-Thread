# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] – 2026-02-07

### Phase 0.1 – Detection (Initial Release)

**Added:**
- ✅ `aether-audit`: Static analysis CLI for detecting thread-safety issues
  - AST-based pattern detection
  - Global variable scanning
  - Class attribute analysis
  - Mutable object identification
- ✅ `aether-proxy`: Thread-safe collection wrappers
  - `ThreadSafeList` with automatic locking
  - `ThreadSafeDict` with automatic locking
  - `ThreadSafeWrapper` base class
  - Dynamic GIL-aware behavior
- ✅ `aether-bench`: Benchmarking suite
  - `Benchmarker` for concurrent performance measurement
  - `BenchmarkRunner` for standard benchmarks
  - Support for GIL state detection
- ✅ Comprehensive test suite
  - Unit tests for audit module
  - Unit tests for proxy module
  - Thread-safety verification tests
- ✅ Documentation
  - Complete README with quick start
  - API documentation
  - Contributing guidelines
  - Example demonstrations

### Features

- **Python 3.9-3.13 Support** – Full compatibility across Python versions
- **Zero External Dependencies** – Pure Python implementation
- **GIL Detection** – Automatic detection of GIL state
- **CLI Tools** – Easy-to-use command-line interfaces
  - `aether-audit` for code analysis
  - `aether-bench` for performance comparison
- **Comprehensive Documentation** – API docs, examples, and guides

### Known Limitations

- Phase 0.5 features not yet implemented
  - `@thread_safe` decorator pending
- Phase 1.0 optimizations not yet available
  - Dynamic lock/lock-free switching not yet enabled

---

## Planned Releases

### [0.5.0] – Q2 2026 – Mitigation Phase

**Planned:**
- `@thread_safe` decorator for automatic lock injection
- Decorator configuration options
- Custom synchronization strategies
- Enhanced pattern detection
- Performance profiling tools

### [1.0.0] – Q3 2026 – Optimization Phase

**Planned:**
- `sys._is_gil_enabled()` integration
- Dynamic lock-free mode when GIL is enabled
- Lock overhead reduction
- Advanced performance optimization

### [1.5.0] – Q4 2026 – Advanced Phase

**Planned:**
- Async/await pattern support
- Actor model implementation
- Distributed locking
- Advanced concurrency patterns

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- **Major** – Breaking changes (0.x → 1.x)
- **Minor** – New features, backward compatible (x.1 → x.2)
- **Patch** – Bug fixes, backward compatible (x.x.1 → x.x.2)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to Aether-Thread.

