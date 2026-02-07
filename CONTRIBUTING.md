# Contributing to Aether-Thread

Thank you for your interest in contributing to Aether-Thread! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- pip and virtual environment tools

### Setup Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/Aether-Thread.git
   cd Aether-Thread
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e ".[dev]"
   pip install pytest black isort mypy
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Writing Code

1. **Follow PEP 8 style guide**
   ```bash
   black aether_thread/
   isort aether_thread/
   ```

2. **Type hints** – Use type annotations for all functions
   ```python
   def analyze(self, source_code: str) -> ScanResult:
       """Detailed docstring."""
       pass
   ```

3. **Docstrings** – Include comprehensive docstrings
   ```python
   def method(self, param: str) -> int:
       """
       Short description.
       
       Longer description if needed.
       
       Args:
           param: Description of param
           
       Returns:
           Description of return value
           
       Raises:
           ValueError: When something goes wrong
       """
   ```

### Testing

1. **Write tests for all new features**
   ```bash
   python -m pytest tests/
   ```

2. **Test structure**
   ```python
   class TestMyFeature(unittest.TestCase):
       def test_basic_functionality(self):
           """Test description."""
           result = my_function()
           self.assertEqual(result, expected)
   ```

3. **Run specific tests**
   ```bash
   python -m pytest tests/test_audit.py::TestCodeAnalyzer::test_detect_global_mutable_variable
   ```

### Documentation

1. **Update README** if adding user-facing features
2. **Add docstrings** to all public classes and functions
3. **Update CHANGELOG** with your changes

## Submitting Changes

### Before Submitting

1. **Ensure tests pass**
   ```bash
   python -m pytest tests/ -v
   ```

2. **Format code**
   ```bash
   black aether_thread/ tests/
   isort aether_thread/ tests/
   ```

3. **Type check** (if available)
   ```bash
   mypy aether_thread/
   ```

4. **Update documentation**
   - README.md if user-facing
   - Docstrings in code
   - Examples if applicable

### Creating a Pull Request

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description explaining what and why
   - Reference to related issues (#123)
   - Screenshots/benchmarks if applicable

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes.
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Performance improvement
   - [ ] Documentation
   
   ## Testing
   - [ ] Tests added/updated
   - [ ] All tests passing
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex logic
   - [ ] Documentation updated
   ```

## Areas for Contribution

### High Priority
- ✅ Phase 0.5: `@thread_safe` decorator implementation
- ✅ Enhanced pattern detection in audit
- ✅ Performance optimizations
- ✅ Documentation and examples

### Medium Priority
- Performance profiling tools
- Integration tests
- Benchmarking improvements

### Nice to Have
- VS Code extension
- IDE plugins
- Web dashboard for reports

## Reporting Bugs

1. **Use GitHub Issues**
2. **Include**:
   - Python version
   - Aether-Thread version
   - Minimal reproducible example
   - Expected vs actual behavior
   - Error traceback if applicable

### Bug Report Template
```markdown
## Description
Clear description of the bug.

## Reproduction Steps
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen.

## Actual Behavior
What actually happened.

## Environment
- Python: 3.x.x
- Aether-Thread: 0.x.x
- OS: Windows/Linux/macOS
```

## Feature Requests

1. **Use GitHub Issues** with label `enhancement`
2. **Include**:
   - Use case and motivation
   - Proposed solution
   - Potential alternatives
   - Examples

## Code Review Process

Your PR will be reviewed by maintainers. We may:
- Request changes
- Ask clarifying questions
- Suggest improvements
- Run CI/CD checks

Be patient and responsive to feedback!

## Merging Requirements

- ✅ Tests passing
- ✅ Code reviewed and approved
- ✅ Documentation updated
- ✅ No merge conflicts
- ✅ All CI checks passing

## Project Structure

```
aether_thread/
├── audit/          # Static analysis
├── proxy/          # Thread-safe wrappers
├── bench/          # Benchmarking
tests/              # Test suite
examples/           # Usage examples
docs/               # Documentation
```

## Coding Standards

### Naming Conventions
- Classes: `PascalCase` (e.g., `ThreadSafeList`)
- Functions/methods: `snake_case` (e.g., `analyze_code`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
- Private members: `_leading_underscore`

### Comments
- Code comments explain "why", not "what"
- Use clear, concise language
- Keep comments up to date with code

### Functions
- Single responsibility principle
- Keep functions small and focused
- Maximum 50 lines recommended
- Comprehensive docstrings required

## Questions or Need Help?

- 📖 Check existing [discussions](https://github.com/tousif-anwar/Aether-Thread/discussions)
- 💬 Start a new discussion
- 📧 Contact maintainers

---

**Thank you for contributing to Aether-Thread! 🙏**
