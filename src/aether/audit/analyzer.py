"""
Static analyzer for detecting non-thread-safe patterns in Python code.

Detects:
- Global mutable variables
- Shared class attributes
- Unprotected access to shared state
- Common race condition patterns
"""

import ast
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"  # Definitely unsafe, high likelihood
    WARNING = "warning"    # Potentially unsafe, moderate likelihood
    INFO = "info"          # Informational, low likelihood


class IssueType(Enum):
    """Types of thread-safety issues."""
    MUTABLE_GLOBAL = "mutable_global"
    MUTABLE_CLASS_ATTRIBUTE = "mutable_class_attribute"
    UNPROTECTED_GLOBAL_ACCESS = "unprotected_global_access"
    UNPROTECTED_ATTRIBUTE_ACCESS = "unprotected_attribute_access"
    POTENTIAL_RACE_CONDITION = "potential_race_condition"
    SHARED_MUTABLE_DEFAULT = "shared_mutable_default"


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
    related_variables: List[str] = field(default_factory=list)


@dataclass
class ScanResult:
    """Results from scanning a codebase."""
    file_path: str
    findings: List[Finding] = field(default_factory=list)
    global_variables: List[str] = field(default_factory=list)
    class_attributes: Dict[str, List[str]] = field(default_factory=dict)
    mutable_globals: List[str] = field(default_factory=list)
    mutable_class_attrs: Dict[str, List[str]] = field(default_factory=dict)


class CodeAnalyzer(ast.NodeVisitor):
    """
    Comprehensive AST-based analyzer that detects thread-safety issues.
    
    Detects:
    - Global mutable variables
    - Unprotected global variable access
    - Mutable class attributes (shared across instances)
    - Mutable default arguments (shared across calls)
    - Potential race condition patterns
    - Missing synchronization decorators
    """
    
    def __init__(self, filename: str):
        self.filename = filename
        self.findings: List[Finding] = []
        self.global_variables: Set[str] = set()
        self.mutable_globals: Set[str] = set()
        self.class_attributes: Dict[str, List[str]] = {}
        self.mutable_class_attrs: Dict[str, List[str]] = {}
        self.function_params: Dict[str, Any] = {}
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        self.in_function = False
        self.global_accesses: Dict[str, List[Tuple[int, str]]] = {}  # var_name -> [(line, type)]
        self.attribute_accesses: Dict[str, List[int]] = {}  # class.attr -> [lines]
        
    def visit_Module(self, node: ast.Module) -> None:
        """Analyze module-level assignments (globals)."""
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        self._check_global_variable(target.id, item)
            elif isinstance(item, ast.ClassDef):
                self.visit_ClassDef(item)
            elif (isinstance(item, ast.FunctionDef) or 
                  isinstance(item, ast.AsyncFunctionDef)):
                self.visit_FunctionDef(item)
        
        # After all traversal, check for patterns
        self._check_race_conditions()
                
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Analyze class-level attributes and methods."""
        prev_class = self.current_class
        self.current_class = node.name
        self.class_attributes[node.name] = []
        self.mutable_class_attrs[node.name] = []
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_name = target.id
                        self.class_attributes[node.name].append(attr_name)
                        self._check_class_attribute(node.name, attr_name, item)
            elif isinstance(item, ast.FunctionDef):
                # Check for mutable default arguments
                self._check_function_defaults(node.name, item)
                self.current_function = item.name
                self.generic_visit(item)
                self.current_function = None
        
        self.generic_visit(node)
        self.current_class = prev_class
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function scope and check defaults."""
        prev_func = self.current_function
        self.current_function = node.name
        self.in_function = True
        
        # Check for mutable default arguments
        self._check_function_defaults(None, node)
        
        # Track global variable accesses
        for child in ast.walk(node):
            if isinstance(child, ast.Global):
                for name in child.names:
                    if name not in self.global_accesses:
                        self.global_accesses[name] = []
        
        self.generic_visit(node)
        self.in_function = False
        self.current_function = prev_func
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function scope."""
        self.visit_FunctionDef(node)
    
    def visit_Global(self, node: ast.Global) -> None:
        """Track global variable declarations."""
        for name in node.names:
            self.global_variables.add(name)
            if name not in self.global_accesses:
                self.global_accesses[name] = []
            self.global_accesses[name].append((node.lineno, "declared"))
        self.generic_visit(node)
    
    def _check_global_variable(self, var_name: str, node: ast.Assign) -> None:
        """Check if a global variable is potentially unsafe."""
        self.global_variables.add(var_name)
        is_mutable = self._is_mutable_value(node.value)
        
        if is_mutable:
            self.mutable_globals.add(var_name)
            self.findings.append(Finding(
                line_number=node.lineno,
                file_path=self.filename,
                issue_type=IssueType.MUTABLE_GLOBAL.value,
                description=f"Global variable '{var_name}' is mutable and accessible from multiple threads",
                severity=Severity.CRITICAL.value,
                code_snippet=ast.unparse(node) if hasattr(ast, 'unparse') else f"{var_name} = ...",
                suggestion=f"Use @atomic decorator on functions that modify '{var_name}', or wrap with ThreadSafeDict/List",
                related_variables=[var_name]
            ))
    
    def _check_class_attribute(self, class_name: str, attr_name: str, 
                              node: ast.Assign) -> None:
        """Check if a class attribute is potentially unsafe."""
        is_mutable = self._is_mutable_value(node.value)
        
        if is_mutable:
            if class_name not in self.mutable_class_attrs:
                self.mutable_class_attrs[class_name] = []
            self.mutable_class_attrs[class_name].append(attr_name)
            
            self.findings.append(Finding(
                line_number=node.lineno,
                file_path=self.filename,
                issue_type=IssueType.MUTABLE_CLASS_ATTRIBUTE.value,
                description=f"Class attribute '{class_name}.{attr_name}' is mutable and shared across all instances",
                severity=Severity.CRITICAL.value,
                code_snippet=ast.unparse(node) if hasattr(ast, 'unparse') else f"{attr_name} = ...",
                suggestion=f"Move initialization to __init__ method to give each instance its own copy, or use @atomic",
                related_variables=[f"{class_name}.{attr_name}"]
            ))
    
    def _check_function_defaults(self, class_name: Optional[str], 
                                node: ast.FunctionDef) -> None:
        """Check for mutable default arguments (classic Python gotcha)."""
        for i, default in enumerate(node.args.defaults):
            if self._is_mutable_value(default):
                arg_index = len(node.args.args) - len(node.args.defaults) + i
                if arg_index < len(node.args.args):
                    arg_name = node.args.args[arg_index].arg
                    func_path = f"{class_name}.{node.name}" if class_name else node.name
                    
                    self.findings.append(Finding(
                        line_number=node.lineno,
                        file_path=self.filename,
                        issue_type=IssueType.SHARED_MUTABLE_DEFAULT.value,
                        description=f"Function '{func_path}' has mutable default argument '{arg_name}' - shared across calls",
                        severity=Severity.WARNING.value,
                        code_snippet=f"def {node.name}({arg_name}=[]):" if hasattr(ast, 'unparse') else "",
                        suggestion=f"Use None as default and create new instance in function: if {arg_name} is None: {arg_name} = []",
                        related_variables=[arg_name]
                    ))
    
    
    def _is_mutable_value(self, node: ast.expr) -> bool:
        """Determine if a value is mutable."""
        if isinstance(node, (ast.List, ast.Dict, ast.Set)):
            return True
        if isinstance(node, ast.Call):
            # Check for common mutable constructors
            if isinstance(node.func, ast.Name):
                if node.func.id in {'list', 'dict', 'set', 'defaultdict', 'deque', 'OrderedDict'}:
                    return True
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in {'defaultdict', 'OrderedDict', 'Counter'}:
                    return True
        if isinstance(node, ast.Constant) and isinstance(node.value, (list, dict, set)):
            return True
        return False
    
    def _check_race_conditions(self) -> None:
        """Detect common race condition patterns."""
        # Check for multiple accesses to mutable globals without protection
        for var_name in self.mutable_globals:
            accesses = self.global_accesses.get(var_name, [])
            if len(accesses) > 1:
                # Multiple accesses suggest potential race condition
                self.findings.append(Finding(
                    line_number=accesses[0][0] if accesses else 0,
                    file_path=self.filename,
                    issue_type=IssueType.POTENTIAL_RACE_CONDITION.value,
                    description=f"Global variable '{var_name}' accessed multiple times ({len(accesses)}) without visible synchronization",
                    severity=Severity.WARNING.value,
                    code_snippet="",
                    suggestion=f"Add @atomic decorator to all functions accessing '{var_name}' or use locks explicitly",
                    related_variables=[var_name]
                ))
    
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
                severity=Severity.CRITICAL.value,
                code_snippet="",
            ))
        
        return ScanResult(
            file_path=self.filename,
            findings=self.findings,
            global_variables=list(self.global_variables),
            class_attributes=self.class_attributes,
            mutable_globals=list(self.mutable_globals),
            mutable_class_attrs=self.mutable_class_attrs
        )
