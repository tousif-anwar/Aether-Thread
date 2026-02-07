"""
Enhanced threat detection for free-threaded Python (3.13+).

Detects code patterns that are safe in standard Python but dangerous
when GIL is disabled:
- Frame.f_locals accesses (can crash interpreter)
- Warning filter issues (thread-safety problems)  
- Shared iterator usage (duplicate/missing elements)
- Async/await patterns incompatible with threading
"""

import ast
from typing import List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FreeThreadThreat(Enum):
    """Types of threats specific to free-threaded Python."""
    FRAME_LOCALS_ACCESS = "frame_locals_access"          # f_locals access - CRASH RISK
    WARNING_CATCH_CONTEXT = "warning_catch_context"      # catch_warnings - RACE RISK
    SHARED_ITERATOR = "shared_iterator"                  # Shared iterators - DATA LOSS RISK
    ASYNC_THREADING_MIX = "async_threading_mix"          # Mixing async/threading - DEADLOCK RISK
    SIGNAL_HANDLER_SHARED_STATE = "signal_handler_race"  # Signal handlers + shared state
    EXCEPTION_GROUP_RACE = "exception_group_race"        # ExceptionGroup in threaded code


@dataclass
class FreeThreadFinding:
    """Finding specific to free-threaded Python."""
    threat_type: str
    line_number: int
    file_path: str
    description: str
    severity: str  # "critical", "high", "medium"
    code_snippet: str
    crash_risk: bool  # True if could crash interpreter
    fix_suggestion: str
    affected_variables: List[str]


class FreeThreadDetector(ast.NodeVisitor):
    """
    Detects code patterns dangerous in free-threaded Python.
    
    Critical patterns:
    1. Frame.f_locals access - can crash interpreter
    2. warnings.catch_warnings without @contextmanager
    3. Shared iterators between threads
    4. Mixing async/await with threading
    5. Signal handlers modifying shared state
    """
    
    def __init__(self, filename: str):
        self.filename = filename
        self.findings: List[FreeThreadFinding] = []
        self.shared_state_vars: Set[str] = set()
        self.iterators: Set[str] = set()
        self.in_async_function = False
        self.in_signal_handler = False
        self.frame_accesses: List[Tuple[int, str]] = []
        
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Detect f_locals and other dangerous frame accesses."""
        # Check for frame.f_locals
        if isinstance(node.value, ast.Name):
            if node.value.id in ('frame', '_frame', 'sys._getframe'):
                if node.attr in ('f_locals', 'f_globals', 'f_builtins'):
                    self.findings.append(FreeThreadFinding(
                        threat_type=FreeThreadThreat.FRAME_LOCALS_ACCESS.value,
                        line_number=node.lineno,
                        file_path=self.filename,
                        description=f"Access to frame.{node.attr} is NOT thread-safe in free-threaded Python - can crash the interpreter",
                        severity="critical",
                        code_snippet=f"frame.{node.attr}",
                        crash_risk=True,
                        fix_suggestion=f"Avoid accessing frame.{node.attr}. Use locals() or globals() instead, but use with caution in threaded code.",
                        affected_variables=[node.value.id]
                    ))
                    self.frame_accesses.append((node.lineno, node.attr))
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Detect dangerous function calls like warnings.catch_warnings()."""
        # Check for warnings.catch_warnings()
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'warnings' and node.func.attr == 'catch_warnings':
                    self.findings.append(FreeThreadFinding(
                        threat_type=FreeThreadThreat.WARNING_CATCH_CONTEXT.value,
                        line_number=node.lineno,
                        file_path=self.filename,
                        description="warnings.catch_warnings() requires manual thread-safety in free-threaded Python",
                        severity="high",
                        code_snippet="warnings.catch_warnings()",
                        crash_risk=False,
                        fix_suggestion="Use a threading.Lock around catch_warnings() if used in threaded code",
                        affected_variables=['warnings']
                    ))
        
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For) -> None:
        """Detect shared iterator usage."""
        # Track iterators
        if isinstance(node.target, ast.Name):
            self.iterators.add(node.target.id)
        
        # Check if iterator is used in shared context
        if isinstance(node.iter, ast.Name):
            iter_name = node.iter.id
            if iter_name in self.shared_state_vars:
                self.findings.append(FreeThreadFinding(
                    threat_type=FreeThreadThreat.SHARED_ITERATOR.value,
                    line_number=node.lineno,
                    file_path=self.filename,
                    description=f"Shared iterator '{iter_name}' used across threads - may return duplicate or missing elements",
                    severity="high",
                    code_snippet=f"for ... in {iter_name}:",
                    crash_risk=False,
                    fix_suggestion="Create thread-local iterators or use thread-safe iteration with locks",
                    affected_variables=[iter_name]
                ))
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async functions to detect async/threading mix."""
        prev_async = self.in_async_function
        self.in_async_function = True
        
        # Check for any threading usage inside async functions
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name):
                        if child.func.value.id in ('threading', 'Thread'):
                            self.findings.append(FreeThreadFinding(
                                threat_type=FreeThreadThreat.ASYNC_THREADING_MIX.value,
                                line_number=child.lineno,
                                file_path=self.filename,
                                description=f"Mixing async/await with threading.{child.func.attr} is dangerous - can cause deadlocks",
                                severity="high",
                                code_snippet="threading code inside async function",
                                crash_risk=False,
                                fix_suggestion="Use asyncio instead of threading, or restructure to keep async and threading separate",
                                affected_variables=['threading']
                            ))
        
        self.generic_visit(node)
        self.in_async_function = prev_async
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Detect signal handlers."""
        # Simple heuristic: if function name suggests signal handler
        if 'signal' in node.name.lower() or 'handler' in node.name.lower():
            # Check if it modifies shared state
            modifiers = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name):
                            modifiers.add(target.id)
                            if target.id in self.shared_state_vars:
                                self.findings.append(FreeThreadFinding(
                                    threat_type=FreeThreadThreat.SIGNAL_HANDLER_SHARED_STATE.value,
                                    line_number=child.lineno,
                                    file_path=self.filename,
                                    description=f"Signal handler modifies shared state '{target.id}' - RACE CONDITION in free-threaded Python",
                                    severity="critical",
                                    code_snippet=f"{target.id} = ...",
                                    crash_risk=True,
                                    fix_suggestion="Move shared state modification to main thread using a queue or event",
                                    affected_variables=[target.id]
                                ))
        
        self.generic_visit(node)
    
    def detect(self, source_code: str) -> List[FreeThreadFinding]:
        """Analyze source code for free-threading threats."""
        try:
            tree = ast.parse(source_code)
            self.visit(tree)
        except SyntaxError:
            pass
        
        return self.findings
