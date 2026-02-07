"""
Tests for the ThreadSafetyAnalyzer.
"""

import pytest
from aether_thread.analyzer import ThreadSafetyAnalyzer, SafetyIssue


def test_analyzer_initialization():
    """Test that analyzer initializes correctly."""
    analyzer = ThreadSafetyAnalyzer()
    assert analyzer.issues == []
    assert len(analyzer.global_vars) == 0


def test_analyze_safe_code():
    """Test analyzing code with no issues."""
    code = """
def safe_function(x, y):
    return x + y
"""
    analyzer = ThreadSafetyAnalyzer()
    issues = analyzer.analyze_code(code)
    assert len(issues) == 0


def test_detect_global_write():
    """Test detection of global variable writes."""
    code = """
global counter
counter = 0

def increment():
    global counter
    counter += 1
"""
    analyzer = ThreadSafetyAnalyzer()
    issues = analyzer.analyze_code(code)
    
    # Should detect at least the augmented assignment
    assert len(issues) > 0
    assert any('counter' in issue.message for issue in issues)


def test_detect_dangerous_functions():
    """Test detection of eval/exec usage."""
    code = """
def dangerous():
    eval("print('hello')")
"""
    analyzer = ThreadSafetyAnalyzer()
    issues = analyzer.analyze_code(code)
    
    assert len(issues) > 0
    assert any('eval' in issue.message for issue in issues)


def test_syntax_error_handling():
    """Test handling of syntax errors."""
    code = "def broken("  # Incomplete syntax
    analyzer = ThreadSafetyAnalyzer()
    issues = analyzer.analyze_code(code)
    
    assert len(issues) > 0
    assert issues[0].severity == 'critical'


def test_get_summary():
    """Test summary generation."""
    code = """
import threading

global x
x = 0

def test():
    global x
    x = 1
"""
    analyzer = ThreadSafetyAnalyzer()
    analyzer.analyze_code(code)
    summary = analyzer.get_summary()
    
    assert 'total_issues' in summary
    assert 'uses_threading' in summary
    assert summary['uses_threading'] is True


def test_analyze_function():
    """Test analyzing a function object."""
    def test_func():
        return 42
    
    analyzer = ThreadSafetyAnalyzer()
    issues = analyzer.analyze_function(test_func)
    
    # Should work without errors
    assert isinstance(issues, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
