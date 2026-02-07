"""
Scanner for recursively analyzing Python codebases.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from .analyzer import CodeAnalyzer, ScanResult, Finding


class StaticScanner:
    """
    Recursively scans Python files in a directory and identifies thread-safety issues.
    """
    
    def __init__(self, exclude_dirs: List[str] = None):
        """
        Initialize the scanner.
        
        Args:
            exclude_dirs: List of directory names to exclude (e.g., '.venv', '__pycache__')
        """
        self.exclude_dirs = exclude_dirs or ['.venv', 'venv', '__pycache__', '.git', '.pytest_cache', 'node_modules']
        self.results: Dict[str, ScanResult] = {}
        self.total_findings: List[Finding] = []
    
    def scan(self, root_path: str) -> Dict[str, ScanResult]:
        """
        Scan a directory for Python files with thread-safety issues.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            Dictionary mapping file paths to scan results
        """
        root = Path(root_path)
        
        if not root.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")
        
        python_files = self._find_python_files(root)
        
        for py_file in python_files:
            self._scan_file(py_file)
        
        return self.results
    
    def _find_python_files(self, root: Path) -> List[Path]:
        """Find all Python files in a directory tree."""
        python_files = []
        
        for entry in root.rglob('*.py'):
            # Skip excluded directories
            if any(excluded in entry.parts for excluded in self.exclude_dirs):
                continue
            python_files.append(entry)
        
        return sorted(python_files)
    
    def _scan_file(self, file_path: Path) -> None:
        """Scan a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            analyzer = CodeAnalyzer(str(file_path))
            result = analyzer.analyze(source_code)
            
            self.results[str(file_path)] = result
            self.total_findings.extend(result.findings)
            
        except (IOError, UnicodeDecodeError) as e:
            print(f"Error reading file {file_path}: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of scanning results."""
        critical_count = sum(1 for f in self.total_findings if f.severity == "critical")
        warning_count = sum(1 for f in self.total_findings if f.severity == "warning")
        info_count = sum(1 for f in self.total_findings if f.severity == "info")
        
        return {
            "total_files_scanned": len(self.results),
            "total_findings": len(self.total_findings),
            "critical": critical_count,
            "warnings": warning_count,
            "info": info_count,
            "files_with_issues": sum(1 for r in self.results.values() if r.findings),
        }
    
    def print_report(self) -> None:
        """Print a formatted report of all findings."""
        summary = self.get_summary()
        
        print("\n" + "="*80)
        print("AETHER-AUDIT REPORT")
        print("="*80)
        print(f"\nSummary:")
        print(f"  Total files scanned: {summary['total_files_scanned']}")
        print(f"  Total findings: {summary['total_findings']}")
        print(f"    - Critical: {summary['critical']}")
        print(f"    - Warnings: {summary['warnings']}")
        print(f"    - Info: {summary['info']}")
        print(f"  Files with issues: {summary['files_with_issues']}")
        
        if self.total_findings:
            print("\n" + "-"*80)
            print("Findings:")
            print("-"*80)
            
            current_file = None
            for finding in sorted(self.total_findings, key=lambda f: (f.file_path, f.line_number)):
                if finding.file_path != current_file:
                    current_file = finding.file_path
                    print(f"\n{current_file}")
                
                severity_icon = {
                    "critical": "🔴",
                    "warning": "🟡",
                    "info": "🔵"
                }.get(finding.severity, "⚪")
                
                print(f"  {severity_icon} Line {finding.line_number}: [{finding.issue_type}]")
                print(f"     {finding.description}")
                if finding.suggestion:
                    print(f"     💡 Suggestion: {finding.suggestion}")
        
        print("\n" + "="*80)
