"""
aether.audit: Comprehensive static analysis for thread-safety issues.

This module provides three complementary detection systems:

1. SHARED STATE DETECTOR
   - Identifies global mutable variables
   - Detects mutable class attributes
   - Finds mutable default arguments
   
2. RACE CONDITION SIMULATOR  
   - Detects check-then-act patterns (TOCTOU)
   - Identifies read-modify-write operations
   - Finds unsynchronized compound assignments
   
3. AUTO-LOCK INJECTOR
   - Suggests @atomic decorator placement
   - Recommends ThreadSafe collection wrappers
   - Provides explicit lock patterns

Example:
    >>> from aether.audit import audit_code
    >>> code = '''
    ... global counter
    ... def increment():
    ...     global counter
    ...     counter += 1  # Race condition!
    ... '''
    >>> report = audit_code(code, "example.py")
    >>> print(report)
"""

from .analyzer import CodeAnalyzer, Finding, ScanResult, Severity, IssueType
from .scanner import StaticScanner
from .race_detector import RaceConditionDetector, RaceConditionFinding, RacePattern
from .lock_injector import AutoLockInjector, LockSuggestion, InjectionReport
from .reporter import AuditReporter, quick_report
from typing import List, Optional, Dict


def audit_code(source_code: str, filename: str = "unknown.py") -> str:
    """
    Quick audits code and returns a formatted report.
    
    This is the main entry point for one-shot code auditing.
    
    Args:
        source_code: Python source code to audit
        filename: Optional filename for error messages
        
    Returns:
        Formatted audit report as a string
        
    Example:
        >>> code = '''
        ... global shared_list
        ... shared_list = []
        ... def append_item(item):
        ...     shared_list.append(item)
        ... '''
        >>> print(audit_code(code, "example.py"))
    """
    # Run all three detectors
    analyzer = CodeAnalyzer(filename)
    analysis = analyzer.analyze(source_code)
    
    race_detector = RaceConditionDetector(filename)
    race_findings = race_detector.detect(source_code)
    
    # Generate reports
    reporter = AuditReporter()
    
    report = f"\n{'='*80}\n"
    report += f"AETHER-AUDIT REPORT: {filename}\n"
    report += f"{'='*80}\n"
    
    # Static analysis findings
    if analysis.findings:
        report += f"\n🔴 SHARED STATE ISSUES ({len(analysis.findings)} found):\n"
        report += f"{'-'*80}\n"
        for finding in analysis.findings:
            report += f"  Line {finding.line_number}: {finding.description}\n"
            if finding.suggestion:
                report += f"  → Fix: {finding.suggestion}\n"
            report += "\n"
    else:
        report += "\n✓ No shared state issues detected.\n"
    
    # Race condition findings
    if race_findings:
        report += f"\n🟡 RACE CONDITIONS ({len(race_findings)} patterns found):\n"
        report += f"{'-'*80}\n"
        for finding in race_findings:
            report += f"  Line {finding.line_numbers[0]}: {finding.description}\n"
            report += f"  → Fix: {finding.fix_suggestion}\n\n"
    else:
        report += "\n✓ No obvious race condition patterns detected.\n"
    
    # Summary statistics
    mutable_global_count = len(analysis.mutable_globals)
    mutable_class_count = sum(len(attrs) for attrs in analysis.mutable_class_attrs.values())
    
    report += f"\n{'='*80}\n"
    report += f"SUMMARY:\n"
    report += f"  Mutable Globals: {mutable_global_count}\n"
    report += f"  Mutable Class Attributes: {mutable_class_count}\n"
    report += f"  Race Conditions: {len(race_findings)}\n"
    report += f"  Total Issues: {len(analysis.findings) + len(race_findings)}\n"
    report += f"{'='*80}\n"
    
    return report


def audit_directory(directory_path: str, exclude_dirs: Optional[List[str]] = None) -> str:
    """
    Audit an entire directory recursively.
    
    Args:
        directory_path: Root directory to scan
        exclude_dirs: Directories to exclude from scan
        
    Returns:
        Comprehensive audit report
    """
    scanner = StaticScanner(exclude_dirs=exclude_dirs)
    results = scanner.scan(directory_path)
    
    reporter = AuditReporter()
    return reporter.report_findings(list(results.values()))


__all__ = [
    # Analyzer exports
    "CodeAnalyzer",
    "Finding",
    "ScanResult",
    "Severity",
    "IssueType",
    
    # Scanner exports
    "StaticScanner",
    
    # Race detector exports
    "RaceConditionDetector",
    "RaceConditionFinding",
    "RacePattern",
    
    # Lock injector exports
    "AutoLockInjector",
    "LockSuggestion",
    "InjectionReport",
    
    # Reporter exports
    "AuditReporter",
    "quick_report",
    
    # Main functions
    "audit_code",
    "audit_directory",
]
