"""
Static analyzer for detecting non-thread-safe patterns in Python code.
"""

import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Finding:
    """Represents a thread-safety issue found in the code."""
    line_number: int
    file_path: str
    issue_type: str
    description: str
    severity: str  # "critical", "warning", "info"
    code_snippet: str
    suggestion: Optional[str] = None


@dataclass
class ScanResult:
    """Results from scanning a codebase."""
    file_path: str
    findings: List[Finding] = field(default_factory=list)
    global_variables: List[str] = field(default_factory=list)
    class_attributes: List[str] = field(default_factory=list)


class CodeAnalyzer(ast.NodeVisitor):
    """
    AST-based analyzer that detects potential thread-safety issues.
    
    Detects:
    - Global variables (especially mutable ones)
    - Class-level mutable attributes without synchronization
    - Shared state patterns
    """
    
    def __init__(self, filename: str):
        self.filename = filename
        self.findings: List[Finding] = []
        self.global_variables: List[str] = []
        self.class_attributes: Dict[str, List[str]] = {}
        self.current_class: Optional[str] = None
        self.in_function = False
        
    def visit_Module(self, node: ast.Module) -> None:
        """Analyze module-level assignments (globals)."""
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        self._check_global_variable(target.id, item)
            elif isinstance(item, ast.ClassDef):
                self.visit_ClassDef(item)
            elif isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                self.generic_visit(item)
                
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Analyze class-level attributes."""
        prev_class = self.current_class
        self.current_class = node.name
        self.class_attributes[node.name] = []
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_name = target.id
                        self.class_attributes[node.name].append(attr_name)
                        self._check_class_attribute(node.name, attr_name, item)
        
        self.generic_visit(node)
        self.current_class = prev_class
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function scope."""
        self.in_function = True
        self.generic_visit(node)
        self.in_function = False
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function scope."""
        self.in_function = True
        self.generic_visit(node)
        self.in_function = False
    
    def _check_global_variable(self, var_name: str, node: ast.Assign) -> None:
        """Check if a global variable is potentially unsafe."""
        self.global_variables.append(var_name)
        
        # Check if the value is mutable
        is_mutable = self._is_mutable_value(node.value)
        
        if is_mutable:
            self.findings.append(Finding(
                line_number=node.lineno,
                file_path=self.filename,
                issue_type="mutable_global",
                description=f"Global variable '{var_name}' is mutable and not synchronized",
                severity="critical",
                code_snippet=ast.unparse(node),
                suggestion=f"Use a thread-safe wrapper or protect access with a Lock"
            ))
    
    def _check_class_attribute(self, class_name: str, attr_name: str, node: ast.Assign) -> None:
        """Check if a class attribute is potentially unsafe."""
        is_mutable = self._is_mutable_value(node.value)
        
        if is_mutable:
            self.findings.append(Finding(
                line_number=node.lineno,
                file_path=self.filename,
                issue_type="mutable_class_attribute",
                description=f"Class attribute '{class_name}.{attr_name}' is mutable and shared across instances",
                severity="critical",
                code_snippet=ast.unparse(node),
                suggestion=f"Move to __init__ or use a thread-safe wrapper"
            ))
    
    def _is_mutable_value(self, node: ast.expr) -> bool:
        """Determine if a value is mutable."""
        if isinstance(node, (ast.List, ast.Dict, ast.Set)):
            return True
        if isinstance(node, ast.Call):
            # Check for common mutable constructors
            if isinstance(node.func, ast.Name):
                if node.func.id in {'list', 'dict', 'set', 'defaultdict'}:
                    return True
        return False
    
    def analyze(self, source_code: str) -> ScanResult:
        """Parse and analyze source code."""
        try:
            tree = ast.parse(source_code)
            self.visit(tree)
        except SyntaxError as e:
            self.findings.append(Finding(
                line_number=e.lineno or 0,
                file_path=self.filename,
                issue_type="syntax_error",
                description=f"Syntax error: {e.msg}",
                severity="critical",
                code_snippet="",
            ))
        
        return ScanResult(
            file_path=self.filename,
            findings=self.findings,
            global_variables=self.global_variables,
            class_attributes=list(self.class_attributes.keys())
        )
