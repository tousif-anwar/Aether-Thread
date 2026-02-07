"""
Thread Safety Analyzer - Detects GIL-dependent patterns and thread-safety issues.
"""

import ast
import inspect
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass


@dataclass
class SafetyIssue:
    """Represents a thread-safety issue found in code."""
    
    severity: str  # 'critical', 'warning', 'info'
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None


class ThreadSafetyAnalyzer(ast.NodeVisitor):
    """
    Analyzes Python code for thread-safety issues and GIL-dependent patterns.
    
    This analyzer identifies common patterns that may cause issues in GIL-free
    environments, such as:
    - Global variable access without locks
    - Non-thread-safe built-in operations
    - Race conditions
    - Shared mutable state
    """
    
    # Patterns that are potentially unsafe in multi-threaded environments
    UNSAFE_GLOBALS = {
        'dict', 'list', 'set', 'collections.defaultdict',
        'collections.deque', 'collections.Counter'
    }
    
    # Thread-safe alternatives
    THREAD_SAFE_ALTERNATIVES = {
        'dict': 'threading.Lock + dict or queue.Queue',
        'list': 'threading.Lock + list or queue.Queue',
        'set': 'threading.Lock + set',
        'collections.defaultdict': 'threading.Lock + collections.defaultdict',
    }
    
    def __init__(self) -> None:
        self.issues: List[SafetyIssue] = []
        self.global_vars: Set[str] = set()
        self.global_writes: Set[str] = set()
        self.imports: Set[str] = set()
        
    def analyze_code(self, code: str, filename: str = "<string>") -> List[SafetyIssue]:
        """
        Analyze Python source code for thread-safety issues.
        
        Args:
            code: Python source code as a string
            filename: Optional filename for error reporting
            
        Returns:
            List of SafetyIssue objects describing potential problems
        """
        try:
            tree = ast.parse(code, filename=filename)
            self.visit(tree)
        except SyntaxError as e:
            self.issues.append(SafetyIssue(
                severity='critical',
                message=f"Syntax error: {e}",
                line_number=e.lineno,
                column=e.offset
            ))
        return self.issues
    
    def analyze_function(self, func: Any) -> List[SafetyIssue]:
        """
        Analyze a Python function for thread-safety issues.
        
        Args:
            func: A Python function object
            
        Returns:
            List of SafetyIssue objects
        """
        try:
            source = inspect.getsource(func)
            return self.analyze_code(source, filename=f"<{func.__name__}>")
        except (OSError, TypeError):
            self.issues.append(SafetyIssue(
                severity='warning',
                message=f"Could not retrieve source for function {func.__name__}"
            ))
            return self.issues
    
    def visit_Global(self, node: ast.Global) -> None:
        """Track global variable declarations."""
        for name in node.names:
            self.global_vars.add(name)
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Check for assignments to global variables."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id in self.global_vars:
                    self.global_writes.add(target.id)
                    self.issues.append(SafetyIssue(
                        severity='warning',
                        message=f"Global variable '{target.id}' modified without synchronization",
                        line_number=node.lineno,
                        column=node.col_offset,
                        suggestion="Use threading.Lock or threading.RLock to protect global state"
                    ))
        self.generic_visit(node)
    
    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Check for augmented assignments (+=, -=, etc.) to globals."""
        if isinstance(node.target, ast.Name):
            if node.target.id in self.global_vars:
                self.issues.append(SafetyIssue(
                    severity='critical',
                    message=f"Non-atomic operation on global '{node.target.id}'",
                    line_number=node.lineno,
                    column=node.col_offset,
                    suggestion="Use threading.Lock or atomic operations"
                ))
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        """Track imports to identify thread-related modules."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from-imports."""
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Check for potentially unsafe function calls."""
        # Check for eval/exec which can have side effects
        if isinstance(node.func, ast.Name):
            if node.func.id in ('eval', 'exec'):
                self.issues.append(SafetyIssue(
                    severity='warning',
                    message=f"Use of '{node.func.id}' may have unexpected side effects in concurrent code",
                    line_number=node.lineno,
                    column=node.col_offset
                ))
        self.generic_visit(node)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the analysis results.
        
        Returns:
            Dictionary with counts and details of issues found
        """
        critical = sum(1 for i in self.issues if i.severity == 'critical')
        warnings = sum(1 for i in self.issues if i.severity == 'warning')
        info = sum(1 for i in self.issues if i.severity == 'info')
        
        has_threading = any('threading' in imp for imp in self.imports)
        has_multiprocessing = any('multiprocessing' in imp for imp in self.imports)
        
        return {
            'total_issues': len(self.issues),
            'critical': critical,
            'warnings': warnings,
            'info': info,
            'global_writes': len(self.global_writes),
            'uses_threading': has_threading,
            'uses_multiprocessing': has_multiprocessing,
            'is_thread_safe': critical == 0 and warnings == 0,
        }
