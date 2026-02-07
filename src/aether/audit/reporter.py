"""
Beautiful report generation for audit findings.

Generates comprehensive, color-formatted reports of thread-safety issues
with severity levels, code snippets, and actionable suggestions.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from .analyzer import Finding, ScanResult
from .race_detector import RaceConditionFinding
from .lock_injector import LockSuggestion


class AuditReporter:
    """Generates human-readable audit reports."""
    
    # Color codes for terminal output
    COLORS = {
        'CRITICAL': '\033[91m',  # Red
        'WARNING': '\033[93m',   # Yellow
        'INFO': '\033[94m',      # Blue
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',
    }
    
    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors
    
    def _color(self, text: str, color_name: str) -> str:
        """Apply color to text if colors enabled."""
        if not self.use_colors:
            return text
        color = self.COLORS.get(color_name, '')
        reset = self.COLORS['RESET']
        return f"{color}{text}{reset}"
    
    def report_findings(self, results: List[ScanResult]) -> str:
        """Generate report for static analysis findings."""
        lines = [
            self._color("=" * 80, "BOLD"),
            self._color("AETHER AUDIT REPORT - THREAD-SAFETY ANALYSIS", "BOLD"),
            self._color("=" * 80, "BOLD"),
        ]
        
        total_findings = sum(len(r.findings) for r in results)
        total_files = len(results)
        
        lines.append(f"\nScanned {total_files} file(s), found {total_findings} issue(s)\n")
        
        # Group by severity
        findings_by_severity = {'critical': [], 'warning': [], 'info': []}
        for result in results:
            for finding in result.findings:
                severity = finding.severity.lower()
                if severity not in findings_by_severity:
                    findings_by_severity[severity] = []
                findings_by_severity[severity].append((result.file_path, finding))
        
        # Report critical issues first
        for severity in ['critical', 'warning', 'info']:
            if findings_by_severity[severity]:
                color = {'critical': 'CRITICAL', 'warning': 'WARNING', 'info': 'INFO'}[severity]
                lines.append(self._color(f"\n{severity.upper()} ISSUES", "BOLD"))
                lines.append(self._color("-" * 40, color))
                
                for file_path, finding in findings_by_severity[severity]:
                    lines.append(self._format_finding(file_path, finding, color))
        
        lines.append("\n" + self._color("=" * 80, "BOLD"))
        return '\n'.join(lines)
    
    def report_race_conditions(self, findings: List[RaceConditionFinding]) -> str:
        """Generate report for detected race conditions."""
        if not findings:
            return "✓ No obvious race condition patterns detected.\n"
        
        lines = [
            self._color("=" * 80, "BOLD"),
            self._color("RACE CONDITION DETECTION REPORT", "BOLD"),
            self._color("=" * 80, "BOLD"),
        ]
        
        lines.append(f"\nFound {len(findings)} potential race condition(s)\n")
        
        # Group by variable
        by_var = {}
        for finding in findings:
            var = finding.affected_variable
            if var not in by_var:
                by_var[var] = []
            by_var[var].append(finding)
        
        for var_name, var_findings in sorted(by_var.items()):
            lines.append(self._color(f"Variable: {var_name}", "BOLD"))
            lines.append(self._color("-" * 40, "WARNING"))
            
            for finding in var_findings:
                lines.append(f"  Pattern: {finding.pattern_type.upper().replace('_', ' ')}")
                lines.append(f"  Lines: {', '.join(map(str, finding.line_numbers))}")
                lines.append(f"  Description: {finding.description}")
                lines.append(f"  Severity: {self._color(finding.severity.upper(), 'CRITICAL')}")
                lines.append(f"  Fix: {finding.fix_suggestion}")
                lines.append("")
        
        lines.append(self._color("=" * 80, "BOLD"))
        return '\n'.join(lines)
    
    def report_injection_suggestions(self, suggestions: List[LockSuggestion]) -> str:
        """Generate report for lock injection suggestions."""
        if not suggestions:
            return "✓ No lock injections suggested.\n"
        
        lines = [
            self._color("=" * 80, "BOLD"),
            self._color("AUTO-LOCK INJECTION RECOMMENDATIONS", "BOLD"),
            self._color("=" * 80, "BOLD"),
        ]
        
        lines.append(f"\nRecommended {len(suggestions)} automatic synchronization fix(es)\n")
        
        # Group by strategy
        by_strategy = {}
        for suggestion in suggestions:
            strategy = suggestion.suggestion_type
            if strategy not in by_strategy:
                by_strategy[strategy] = []
            by_strategy[strategy].append(suggestion)
        
        strategy_titles = {
            'decorator': '🔒 Decorator Strategy (Easiest - Recommended First)',
            'wrapper': '📦 Collection Wrapper Strategy (For Shared Data Structures)',
            'explicit_lock': '🔐 Explicit Lock Strategy (For Fine-Grained Control)',
        }
        
        for strategy, title in strategy_titles.items():
            if strategy in by_strategy:
                lines.append(self._color(f"\n{title}", "BOLD"))
                lines.append(self._color("-" * 60, strategy_titles[strategy].split()[0]))
                
                for sugg in by_strategy[strategy]:
                    lines.append(f"\n  Target: {sugg.target_name} (line {sugg.location})")
                    lines.append(f"  Explanation: {sugg.explanation}")
                    lines.append(f"\n  Current Code:")
                    for line in sugg.current_code.split('\n')[:2]:
                        lines.append(f"    {line}")
                    lines.append(f"\n  Suggested Code:")
                    for line in sugg.suggested_code.split('\n')[:3]:
                        lines.append(f"    {line}")
                    lines.append("")
        
        lines.append(self._color("=" * 80, "BOLD"))
        return '\n'.join(lines)
    
    def _format_finding(self, file_path: str, finding: Finding, color: str) -> str:
        """Format a single finding for display."""
        lines = [
            f"\n  File: {file_path}",
            f"  Line: {finding.line_number}",
            f"  Type: {finding.issue_type.upper().replace('_', ' ')}",
            f"  {self._color(finding.description, color)}",
        ]
        
        if finding.code_snippet:
            lines.append(f"  Code: {finding.code_snippet}")
        
        if finding.suggestion:
            lines.append(f"  Suggestion: {finding.suggestion}")
        
        if finding.related_variables:
            lines.append(f"  Variables: {', '.join(finding.related_variables)}")
        
        return '\n'.join(lines)
    
    def generate_summary_table(self, results: List[ScanResult]) -> str:
        """Generate a summary table of findings by file."""
        lines = [
            "\n" + self._color("SUMMARY BY FILE", "BOLD"),
            self._color("-" * 80, "BOLD"),
            f"{'File':<40} {'Critical':<12} {'Warnings':<12} {'Info':<12}",
            self._color("-" * 80, "DIM"),
        ]
        
        for result in results:
            critical = sum(1 for f in result.findings if f.severity == 'critical')
            warning = sum(1 for f in result.findings if f.severity == 'warning')
            info = sum(1 for f in result.findings if f.severity == 'info')
            
            file_display = result.file_path.split('/')[-1]  # Just filename
            lines.append(f"{file_display:<40} {critical:<12} {warning:<12} {info:<12}")
        
        lines.append(self._color("-" * 80, "DIM"))
        return '\n'.join(lines)


def quick_report(findings: List[Finding], filename: str = "Unknown") -> str:
    """Generate a quick one-page report of findings."""
    if not findings:
        return f"✓ No thread-safety issues in {filename}\n"
    
    report = f"\n🔍 THREAD-SAFETY AUDIT: {filename}\n"
    report += f"   Found {len(findings)} issue(s):\n"
    
    for f in findings:
        icon = "🔴" if f.severity == "critical" else "🟡" if f.severity == "warning" else "🔵"
        report += f"\n   {icon} {f.description}\n"
        report += f"      Location: line {f.line_number}\n"
        report += f"      Fix: {f.suggestion}\n"
    
    return report
