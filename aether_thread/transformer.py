"""
Code Transformer - Helps transform legacy code to be thread-safe.
"""

import ast
import inspect
from typing import Any, List, Optional


class ThreadSafeTransformer(ast.NodeTransformer):
    """
    AST transformer that adds thread-safety mechanisms to Python code.
    
    This transformer can:
    - Wrap global variable access with locks
    - Convert regular functions to thread-safe versions
    - Add synchronization primitives
    """
    
    def __init__(self) -> None:
        self.global_vars: set = set()
        self.transformations: List[str] = []
        
    def visit_Global(self, node: ast.Global) -> ast.Global:
        """Track global declarations."""
        self.global_vars.update(node.names)
        return node
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Add thread-safe decorator to functions that modify globals."""
        # Check if function modifies any global variables
        modifies_globals = False
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id in self.global_vars:
                        modifies_globals = True
                        break
        
        if modifies_globals:
            # Add @thread_safe decorator
            decorator = ast.Name(id='thread_safe', ctx=ast.Load())
            node.decorator_list.insert(0, decorator)
            self.transformations.append(
                f"Added @thread_safe decorator to function '{node.name}'"
            )
        
        self.generic_visit(node)
        return node


class CodeTransformer:
    """
    Transforms Python code to make it more thread-safe.
    
    This class provides utilities for automatically refactoring code
    to use thread-safe patterns.
    """
    
    def __init__(self) -> None:
        self.transformer = ThreadSafeTransformer()
    
    def transform_code(self, code: str) -> tuple[str, List[str]]:
        """
        Transform Python source code to add thread-safety.
        
        Args:
            code: Python source code as a string
            
        Returns:
            Tuple of (transformed_code, list_of_transformations)
        """
        try:
            tree = ast.parse(code)
            transformed = self.transformer.visit(tree)
            
            # Fix missing locations
            ast.fix_missing_locations(transformed)
            
            # Convert back to code
            transformed_code = ast.unparse(transformed)
            
            return transformed_code, self.transformer.transformations
        except SyntaxError as e:
            return code, [f"Syntax error: {e}"]
    
    def transform_function(self, func: Any) -> tuple[Optional[str], List[str]]:
        """
        Transform a Python function to add thread-safety.
        
        Args:
            func: A Python function object
            
        Returns:
            Tuple of (transformed_source, list_of_transformations)
        """
        try:
            source = inspect.getsource(func)
            return self.transform_code(source)
        except (OSError, TypeError) as e:
            return None, [f"Could not retrieve source: {e}"]
    
    @staticmethod
    def suggest_improvements(code: str) -> List[str]:
        """
        Suggest improvements for thread-safety without modifying code.
        
        Args:
            code: Python source code as a string
            
        Returns:
            List of suggestions
        """
        suggestions = []
        tree = ast.parse(code)
        
        # Check for common patterns
        has_threading = False
        uses_globals = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if 'threading' in alias.name:
                        has_threading = True
            
            if isinstance(node, ast.Global):
                uses_globals = True
        
        if uses_globals and not has_threading:
            suggestions.append(
                "Consider using 'threading.Lock' to protect global variables"
            )
        
        if not has_threading:
            suggestions.append(
                "Import 'threading' module for synchronization primitives"
            )
        
        suggestions.append(
            "Consider using thread-safe data structures from 'queue' module"
        )
        
        suggestions.append(
            "Use 'threading.local()' for thread-local storage instead of globals"
        )
        
        return suggestions
    
    @staticmethod
    def generate_thread_safe_wrapper(function_name: str) -> str:
        """
        Generate a thread-safe wrapper template for a function.
        
        Args:
            function_name: Name of the function to wrap
            
        Returns:
            Python code as a string
        """
        template = f"""
import threading
from functools import wraps

_lock = threading.RLock()

def thread_safe_{function_name}(*args, **kwargs):
    \"\"\"Thread-safe wrapper for {function_name}.\"\"\"
    with _lock:
        return {function_name}(*args, **kwargs)
"""
        return template.strip()
