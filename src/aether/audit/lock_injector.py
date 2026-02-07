"""
Auto-lock injector for thread-safe code generation.

Suggests and generates code that adds synchronization to unsafe patterns:
- Wrapping with @atomic decorator
- Adding explicit lock usage
- Wrapping collections with ThreadSafe variants
"""

import ast
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LockSuggestion:
    """Suggestion for adding synchronization to code."""
    target_name: str              # Variable or function name
    location: int                 # Line number
    suggestion_type: str          # "decorator", "explicit_lock", "wrapper"
    current_code: str             # Current code snippet
    suggested_code: str           # Suggested replacement
    explanation: str              # Why this helps
    file_path: str


class AutoLockInjector:
    """
    Analyzes unsafe code patterns and suggests lock injection strategies.
    
    Strategies:
    1. @atomic decorator - For methods/functions with shared state access
    2. Explicit locks - For complex scenarios needing fine-grained control
    3. ThreadSafe wrappers - For shared collections (list, dict, set)
    """
    
    def __init__(self, filename: str, source_code: str):
        self.filename = filename
        self.source_code = source_code
        self.lines = source_code.split('\n')
        self.suggestions: List[LockSuggestion] = []
        
    def suggest_atomic_for_function(self, func_name: str, line_number: int, 
                                   global_access: bool = False) -> LockSuggestion:
        """Suggest @atomic decorator for a function."""
        current = f"def {func_name}(...):"
        decorator = "@atomic"
        suggested = f"{decorator}\ndef {func_name}(...):"
        
        explanation = (
            f"Function '{func_name}' accesses {'global' if global_access else 'shared'} state. "
            "The @atomic decorator ensures all statements execute atomically without interference."
        )
        
        return LockSuggestion(
            target_name=func_name,
            location=line_number,
            suggestion_type="decorator",
            current_code=current,
            suggested_code=suggested,
            explanation=explanation,
            file_path=self.filename
        )
    
    def suggest_atomic_for_method(self, class_name: str, method_name: str, 
                                 line_number: int) -> LockSuggestion:
        """Suggest @atomic decorator for a class method."""
        current = f"def {method_name}(self):"
        suggested = f"@atomic\n    def {method_name}(self):"
        
        explanation = (
            f"Method '{class_name}.{method_name}' accesses instance state that could be "
            "modified concurrently. @atomic serializes access."
        )
        
        return LockSuggestion(
            target_name=f"{class_name}.{method_name}",
            location=line_number,
            suggestion_type="decorator",
            current_code=current,
            suggested_code=suggested,
            explanation=explanation,
            file_path=self.filename
        )
    
    def suggest_threadsafe_wrapper(self, var_name: str, line_number: int, 
                                  collection_type: str) -> LockSuggestion:
        """Suggest ThreadSafe collection wrapper for shared collections."""
        type_map = {
            'list': 'ThreadSafeList',
            'dict': 'ThreadSafeDict',
            'set': 'ThreadSafeSet',
        }
        
        wrapper_class = type_map.get(collection_type, 'ThreadSafe' + collection_type.title())
        
        current = f"{var_name} = {collection_type}()"
        suggested = f"from aether import {wrapper_class}\n{var_name} = {wrapper_class}()"
        
        explanation = (
            f"Global {collection_type} '{var_name}' is accessed from multiple threads. "
            f"Use {wrapper_class} which automatically synchronizes all operations."
        )
        
        return LockSuggestion(
            target_name=var_name,
            location=line_number,
            suggestion_type="wrapper",
            current_code=current,
            suggested_code=suggested,
            explanation=explanation,
            file_path=self.filename
        )
    
    def suggest_explicit_lock(self, var_name: str, line_number: int) -> LockSuggestion:
        """Suggest explicit lock for fine-grained control."""
        current = f"shared_var = {var_name}"
        suggested = (
            f"import threading\n"
            f"{var_name}_lock = threading.RLock()\n\n"
            f"# Then use:\n"
            f"with {var_name}_lock:\n"
            f"    shared_var = {var_name}"
        )
        
        explanation = (
            f"For complex scenarios with '{var_name}', explicit locks provide fine-grained control. "
            "RLock (reentrant lock) allows the same thread to acquire the lock multiple times."
        )
        
        return LockSuggestion(
            target_name=var_name,
            location=line_number,
            suggestion_type="explicit_lock",
            current_code=current,
            suggested_code=suggested,
            explanation=explanation,
            file_path=self.filename
        )
    
    def analyze_mutable_global(self, var_name: str, line_number: int,
                              var_type: str = "unknown") -> List[LockSuggestion]:
        """Analyze mutable global and suggest fix strategies."""
        suggestions = []
        
        # Strategy 1: If it's a list/dict/set, suggest ThreadSafe wrapper
        if var_type in ('list', 'dict', 'set'):
            suggestions.append(
                self.suggest_threadsafe_wrapper(var_name, line_number, var_type)
            )
        
        # Strategy 2: Suggest explicit lock if more control needed
        suggestions.append(
            self.suggest_explicit_lock(var_name, line_number)
        )
        
        # Strategy 3: If wrapped in functions, suggest @atomic on them
        suggestions.append(LockSuggestion(
            target_name=var_name,
            location=line_number,
            suggestion_type="decorator",
            current_code=f"global {var_name}\n{var_name} = ...",
            suggested_code=f"# Add @atomic decorators to any function/method modifying {var_name}:\n"
                          f"@atomic\ndef update_{var_name}(): ...",
            explanation=f"Add @atomic to all functions that read/modify '{var_name}'",
            file_path=self.filename
        ))
        
        return suggestions
    
    def analyze_unprotected_access(self, var_name: str, access_count: int,
                                  line_number: int) -> List[LockSuggestion]:
        """Analyze unprotected access patterns and suggest fixes."""
        suggestions = []
        
        # Multiple accesses without protection = high priority
        if access_count > 2:
            suggestions.append(LockSuggestion(
                target_name=var_name,
                location=line_number,
                suggestion_type="decorator",
                current_code=f"# Multiple accesses to {var_name} ({access_count} times)",
                suggested_code=f"# RECOMMENDED: Add @atomic to all functions accessing {var_name}",
                explanation=(
                    f"Variable '{var_name}' is accessed {access_count} times without synchronization. "
                    "Add @atomic decorator to minimize lock overhead while ensuring atomicity."
                ),
                file_path=self.filename
            ))
        
        return suggestions
    
    def get_priority_fixes(self) -> List[LockSuggestion]:
        """
        Get critical fixes that should be applied first.
        Returns suggestions prioritized by impact and ease of implementation.
        """
        return sorted(self.suggestions, key=lambda s: (
            0 if s.suggestion_type == "decorator" else 1,  # Decorators easiest
            0 if "critical" in s.explanation.lower() else 1,
        ))
    
    def generate_patched_code(self, suggestion: LockSuggestion) -> str:
        """Generate patched code with applied suggestion."""
        lines = self.lines.copy()
        target_line = suggestion.location - 1  # Convert to 0-based
        
        if 0 <= target_line < len(lines):
            if suggestion.suggestion_type == "decorator":
                # Insert decorator above the target line
                indent = len(lines[target_line]) - len(lines[target_line].lstrip())
                lines.insert(target_line, " " * indent + "@atomic")
            
            elif suggestion.suggestion_type == "wrapper":
                # Replace import section
                for i, line in enumerate(lines):
                    if "import" in line and i < target_line:
                        lines.insert(i + 1, "from aether import ThreadSafeDict, ThreadSafeList, ThreadSafeSet")
                        break
                else:
                    # No import found, add at top
                    lines.insert(0, "from aether import ThreadSafeDict, ThreadSafeList, ThreadSafeSet")
        
        return '\n'.join(lines)


class InjectionReport:
    """Report of suggested injections."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.suggestions: List[LockSuggestion] = []
        self.total_issues = 0
        self.critical_count = 0
        self.recommended_fixes = 0
    
    def add_suggestion(self, suggestion: LockSuggestion) -> None:
        """Add a suggestion to the report."""
        self.suggestions.append(suggestion)
        if "critical" in suggestion.explanation.lower():
            self.critical_count += 1
        self.recommended_fixes += 1
    
    def print_summary(self) -> str:
        """Generate summary of injection recommendations."""
        lines = [
            f"\n{'='*70}",
            f"INJECTION REPORT: {self.filename}",
            f"{'='*70}",
            f"Total Issues Found: {self.total_issues}",
            f"Critical Fixes: {self.critical_count}",
            f"Recommended Injections: {self.recommended_fixes}",
            f"\nTop Priority Strategies:",
        ]
        
        # Group by strategy
        by_type = {}
        for sugg in self.suggestions:
            if sugg.suggestion_type not in by_type:
                by_type[sugg.suggestion_type] = []
            by_type[sugg.suggestion_type].append(sugg)
        
        strategy_order = ["decorator", "wrapper", "explicit_lock"]
        for strategy in strategy_order:
            if strategy in by_type:
                lines.append(f"\n  {strategy.upper().replace('_', ' ')}: {len(by_type[strategy])} suggestions")
                for sugg in by_type[strategy][:2]:  # Show first 2
                    lines.append(f"    - {sugg.target_name} (line {sugg.location})")
        
        lines.append(f"\n{'='*70}\n")
        return '\n'.join(lines)
