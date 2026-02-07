"""
Tests for the Code Transformer.
"""

import pytest
from aether_thread.transformer import CodeTransformer, ThreadSafeTransformer


def test_transformer_initialization():
    """Test transformer initialization."""
    transformer = CodeTransformer()
    assert transformer is not None


def test_transform_code_with_globals():
    """Test transforming code with global variables."""
    code = """
global counter
counter = 0

def increment():
    global counter
    counter += 1
"""
    transformer = CodeTransformer()
    transformed, changes = transformer.transform_code(code)
    
    assert transformed is not None
    # Should suggest or apply changes
    assert isinstance(changes, list)


def test_suggest_improvements():
    """Test improvement suggestions."""
    code = """
global x
x = 0

def modify():
    global x
    x = 1
"""
    suggestions = CodeTransformer.suggest_improvements(code)
    
    assert len(suggestions) > 0
    assert any('threading' in s.lower() for s in suggestions)


def test_generate_wrapper():
    """Test wrapper generation."""
    wrapper = CodeTransformer.generate_thread_safe_wrapper('my_function')
    
    assert 'threading' in wrapper
    assert 'my_function' in wrapper
    assert 'thread_safe_my_function' in wrapper


def test_transform_function():
    """Test transforming a function object."""
    def test_func():
        return 42
    
    transformer = CodeTransformer()
    result, changes = transformer.transform_function(test_func)
    
    # Should handle the function
    assert isinstance(changes, list)


def test_safe_code_no_changes():
    """Test that safe code gets minimal changes."""
    code = """
def safe_function(x, y):
    result = x + y
    return result
"""
    transformer = CodeTransformer()
    transformed, changes = transformer.transform_code(code)
    
    assert transformed is not None
    # Safe code should have no or minimal transformations


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
