"""
Race condition pattern detector using static analysis.

This module identifies common race condition patterns:
- Check-then-act (TOCTOU - Time Of Check To Time Of Use)
- Read-modify-write without synchronization
- Multiple unsynchronized accesses to shared state
"""

import ast
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RacePattern(Enum):
    """Types of race condition patterns detected."""
    CHECK_THEN_ACT = "check_then_act"           # if x: modify(x)
    READ_MODIFY_WRITE = "read_modify_write"     # x = x + 1
    UNSYNCHRONIZED_ACCESS = "unsynchronized_access"  # multiple unguarded accesses
    COMPOUND_OPERATION = "compound_operation"   # += without guard


@dataclass
class RaceConditionFinding:
    """Represents a detected race condition pattern."""
    pattern_type: str
    affected_variable: str
    line_numbers: List[int]
    file_path: str
    description: str
    severity: str  # high, medium, low
    code_lines: List[str]
    fix_suggestion: str


class RaceConditionDetector(ast.NodeVisitor):
    """
    Detects potential race condition patterns in code.
    
    Patterns detected:
    1. Check-Then-Act (TOCTOU): 
       if condition(shared_var):
           modify(shared_var)
    
    2. Read-Modify-Write:
       counter = counter + 1  (without synchronization)
    
    3. Compound Assignment:
       x += 1  (without synchronization)
    """
    
    def __init__(self, filename: str):
        self.filename = filename
        self.findings: List[RaceConditionFinding] = []
        self.shared_variables: Set[str] = set()
        self.current_function: Optional[str] = None
        self.in_conditional: bool = False
        self.accessed_in_conditional: Set[str] = set()
        self.modified_outside_conditional: Set[str] = set()
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Analyze function for race condition patterns."""
        prev_func = self.current_function
        self.current_function = node.name
        
        # Reset per-function state
        self.accessed_in_conditional = set()
        self.modified_outside_conditional = set()
        
        # First pass: find all variable assignments
        for item in node.body:
            self._track_assignments(item)
        
        # Second pass: find conditional accesses followed by modifications
        self._analyze_control_flow(node.body)
        
        self.generic_visit(node)
        self.current_function = prev_func
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Analyze async function for race patterns."""
        self.visit_FunctionDef(node)
    
    def visit_If(self, node: ast.If) -> None:
        """Analyze if statements for check-then-act patterns."""
        # Get variables accessed in condition
        condition_vars = self._get_accessed_variables(node.test)
        
        # Get variables modified in body
        body_vars = self._get_modified_variables(node.body)
        
        # If same variable is checked and then modified, potential race
        overlap = condition_vars & body_vars
        if overlap:
            lines = [node.lineno] + [item.lineno for item in ast.walk(node) 
                                    if hasattr(item, 'lineno')]
            
            for var in overlap:
                self.findings.append(RaceConditionFinding(
                    pattern_type=RacePattern.CHECK_THEN_ACT.value,
                    affected_variable=var,
                    line_numbers=sorted(set(lines))[:3],  # Keep first 3
                    file_path=self.filename,
                    description=f"Check-then-act pattern on '{var}': variable is checked in condition but modified in body without apparent synchronization",
                    severity="high",
                    code_lines=self._extract_code_lines(node),
                    fix_suggestion=f"Wrap both the check and modification of '{var}' with @atomic decorator or explicit lock"
                ))
        
        self.generic_visit(node)
    
    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Detect compound assignments without synchronization."""
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            self.findings.append(RaceConditionFinding(
                pattern_type=RacePattern.COMPOUND_OPERATION.value,
                affected_variable=var_name,
                line_numbers=[node.lineno],
                file_path=self.filename,
                description=f"Compound assignment '{var_name} {ast.unparse(node.op) if hasattr(ast, 'unparse') else ''}= ...' is not atomic",
                severity="high",
                code_lines=[f"{var_name} {self._get_op_symbol(node.op)}= ..."],
                fix_suggestion=f"Use @atomic decorator on function containing '{var_name} {self._get_op_symbol(node.op)}= ...'"
            ))
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Detect read-modify-write patterns."""
        # Check if RHS reads from a variable being written
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_var = node.targets[0].id
            source_vars = self._get_accessed_variables(node.value)
            
            if target_var in source_vars:
                # Read-modify-write pattern: x = x + 1
                self.findings.append(RaceConditionFinding(
                    pattern_type=RacePattern.READ_MODIFY_WRITE.value,
                    affected_variable=target_var,
                    line_numbers=[node.lineno],
                    file_path=self.filename,
                    description=f"Read-modify-write pattern on '{target_var}': variable is read and written in same statement without synchronization",
                    severity="high",
                    code_lines=[self._unparse_node(node)],
                    fix_suggestion=f"Either: (1) Use @atomic decorator, (2) Use threading.Lock explicitly, or (3) Use ThreadSafe wrapper"
                ))
        
        self.generic_visit(node)
    
    def _track_assignments(self, node: ast.stmt) -> None:
        """Track variable assignments in a code block."""
        for item in ast.walk(node):
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        self.shared_variables.add(target.id)
    
    def _get_accessed_variables(self, node: ast.expr) -> Set[str]:
        """Get all variables accessed in an expression."""
        variables = set()
        for item in ast.walk(node):
            if isinstance(item, ast.Name):
                variables.add(item.id)
        return variables
    
    def _get_modified_variables(self, nodes: List[ast.stmt]) -> Set[str]:
        """Get variables modified in a list of statements."""
        variables = set()
        for node in nodes:
            for item in ast.walk(node):
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            variables.add(target.id)
                elif isinstance(item, ast.AugAssign):
                    if isinstance(item.target, ast.Name):
                        variables.add(item.target.id)
        return variables
    
    def _analyze_control_flow(self, body: List[ast.stmt]) -> None:
        """Analyze control flow for problematic patterns."""
        for stmt in body:
            self.visit(stmt)
    
    def _extract_code_lines(self, node: ast.stmt) -> List[str]:
        """Extract code snippet from AST node."""
        try:
            if hasattr(ast, 'unparse'):
                code = ast.unparse(node)
                # Limit to first 3 lines for brevity
                return code.split('\n')[:3]
            return ["[code snippet]"]
        except:
            return ["[code snippet]"]
    
    def _unparse_node(self, node: ast.stmt) -> str:
        """Get string representation of a node."""
        try:
            if hasattr(ast, 'unparse'):
                return ast.unparse(node)
            return "[code]"
        except:
            return "[code]"
    
    def _get_op_symbol(self, op: ast.operator) -> str:
        """Get string representation of an operator."""
        op_map = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.Mod: '%',
            ast.Pow: '**',
            ast.LShift: '<<',
            ast.RShift: '>>',
            ast.BitOr: '|',
            ast.BitXor: '^',
            ast.BitAnd: '&',
            ast.FloorDiv: '//',
        }
        return op_map.get(type(op), '?')
    
    def detect(self, source_code: str) -> List[RaceConditionFinding]:
        """Analyze source code for race condition patterns."""
        try:
            tree = ast.parse(source_code)
            self.visit(tree)
        except SyntaxError:
            pass  # Will be caught by main analyzer
        
        return self.findings
