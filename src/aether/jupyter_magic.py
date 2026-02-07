"""
Jupyter Magic Commands for Aether thread-safety toolkit.

Install with:
  %load_ext aether.jupyter_magic

Then use:
  %%audit                - Check cell code for thread-safety issues
  %%profile_threads      - Profile cell workload to find saturation cliff
  %gil_status            - Quick GIL/environment status
  %%free_threaded_check  - Detect free-threading specific issues
"""

from IPython.core.magic import (register_cell_magic, register_line_magic,
                               Magics, magics_class, cell_magic, line_magic)
from IPython.core.magics_arguments import (argument, magic_arguments,
                                          parse_argstring)
from IPython.display import display, HTML, Markdown
import sys
from typing import Optional
from pathlib import Path

# Import aether modules
try:
    from aether.audit.analyzer import CodeAnalyzer
    from aether.audit.free_thread_detector import FreeThreadDetector
    from aether.profile import SaturationCliffProfiler
    from aether.check import GILStatusChecker
except ImportError:
    # Fallback for development
    sys.path.insert(0, str(Path(__file__).parent))
    from aether.audit.analyzer import CodeAnalyzer
    from aether.audit.free_thread_detector import FreeThreadDetector
    from aether.profile import SaturationCliffProfiler
    from aether.check import GILStatusChecker


@magics_class
class AetherMagics(Magics):
    """IPython magic commands for Aether."""
    
    @cell_magic
    @magic_arguments.magic_arguments()
    @argument('--verbose', '-v', action='store_true', help='Show detailed output')
    def audit(self, line, cell):
        """
        Check cell code for thread-safety issues.
        
        Usage:
            %%audit [--verbose]
            # your code here
        """
        args = parse_argstring(self.audit, line)
        
        try:
            analyzer = CodeAnalyzer('<notebook-cell>')
            findings = analyzer.analyze(cell)
            
            if not findings:
                display(HTML("✅ <b>No thread-safety issues found</b>"))
                return
            
            # Display findings
            html = "<div style='border: 2px solid #ff9800; padding: 10px; border-radius: 5px;'>"
            html += "<h3>🔍 Thread-Safety Issues Found</h3>"
            html += "<ul>"
            
            for finding in findings:
                severity_color = "#ff5252" if finding.severity > 0.7 else "#ffa726"
                severity_icon = "🔴" if finding.severity > 0.7 else "🟡"
                
                html += f"<li style='margin: 8px 0;'>"
                html += f"{severity_icon} <b>{finding.type}</b>: {finding.description}"
                
                if args.verbose:
                    html += f"<br/><code>{finding.code_snippet}</code>"
                    html += f"<br/><small>Line {finding.line_number}</small>"
                
                html += "</li>"
            
            html += "</ul>"
            html += "</div>"
            display(HTML(html))
            
        except Exception as e:
            display(HTML(f"❌ Error: {str(e)}"))
    
    @cell_magic
    @magic_arguments.magic_arguments()
    @argument('--max-threads', type=int, default=16, help='Max threads to test')
    @argument('--duration', type=float, default=2.0, help='Duration per run')
    def profile_threads(self, line, cell):
        """
        Profile cell code to find saturation cliff.
        
        Usage:
            %%profile_threads [--max-threads N] [--duration S]
            def workload():
                # your code here
                pass
        """
        args = parse_argstring(self.profile_threads, line)
        
        try:
            # Execute cell to define workload function
            exec_namespace = {}
            exec(cell, self.shell.user_ns, exec_namespace)
            
            # Find workload function
            workload_fn = None
            for name, obj in exec_namespace.items():
                if callable(obj) and name.startswith('workload'):
                    workload_fn = obj
                    break
            
            if workload_fn is None:
                display(HTML("❌ Cell must define a 'workload()' function"))
                return
            
            # Run profiler
            display(HTML("<p>⏳ Profiling (this may take a moment)...</p>"))
            
            profiler = SaturationCliffProfiler(
                workload_fn,
                duration_per_run=args.duration,
                max_threads=args.max_threads
            )
            analysis = profiler.profile()
            
            # Display results
            html = "<div style='border: 2px solid #4caf50; padding: 10px; border-radius: 5px;'>"
            html += "<h3>⚡ Saturation Cliff Analysis</h3>"
            
            # Chart
            html += "<pre style='background: #f5f5f5; padding: 10px; border-radius: 3px;'>"
            html += analysis.plot_ascii_chart()
            html += "</pre>"
            
            # Statistics
            html += "<table style='border-collapse: collapse; width: 100%;'>"
            html += f"<tr><td><b>Optimal Threads:</b></td><td>{analysis.optimal_threads}</td></tr>"
            html += f"<tr><td><b>Cliff Point:</b></td><td>{analysis.cliff_threads} threads</td></tr>"
            html += f"<tr><td><b>Cliff Severity:</b></td><td>{analysis.cliff_severity*100:.1f}%</td></tr>"
            
            if analysis.recommendations:
                html += f"<tr><td colspan='2'><b>Recommendation:</b> {analysis.recommendations[0]}</td></tr>"
            
            html += "</table></div>"
            display(HTML(html))
            
        except Exception as e:
            display(HTML(f"❌ Error: {str(e)}"))
    
    @cell_magic
    @magic_arguments.magic_arguments()
    @argument('--verbose', '-v', action='store_true', help='Show detailed output')
    def free_threaded_check(self, line, cell):
        """
        Check cell code for free-threaded Python issues.
        
        Usage:
            %%free_threaded_check [--verbose]
            # your code here
        """
        args = parse_argstring(self.free_threaded_check, line)
        
        try:
            detector = FreeThreadDetector('<notebook-cell>')
            threats = detector.detect(cell)
            
            if not threats:
                display(HTML("✅ <b>No free-threaded Python issues found</b>"))
                return
            
            # Display threats
            html = "<div style='border: 2px solid #f44336; padding: 10px; border-radius: 5px;'>"
            html += "<h3>🟢 Free-Threaded Python Issues</h3>"
            html += "<ul>"
            
            for threat in threats:
                icon = "🔴" if threat.crash_risk else "🟠"
                severity = "CRASH RISK" if threat.crash_risk else "SAFETY RISK"
                
                html += f"<li style='margin: 8px 0;'>"
                html += f"{icon} <b>{severity}</b> - {threat.description}"
                html += f"<br/><small>Fix: {threat.recommendation}</small>"
                html += "</li>"
            
            html += "</ul></div>"
            display(HTML(html))
            
        except Exception as e:
            display(HTML(f"❌ Error: {str(e)}"))
    
    @line_magic
    @magic_arguments.magic_arguments()
    @argument('--full', action='store_true', help='Show full report')
    def gil_status(self, line):
        """
        Show current GIL status and environment.
        
        Usage:
            %gil_status [--full]
        """
        args = parse_argstring(self.gil_status, line)
        
        try:
            checker = GILStatusChecker()
            status = checker.get_status()
            
            # Determine status icon and color
            if status.gil_status.value == 'disabled':
                icon = "🟢"
                color = "#4caf50"
                status_text = "DISABLED (Free-Threaded!)"
            elif status.gil_status.value == 'enabled':
                icon = "🔴"
                color = "#f44336"
                status_text = "ENABLED (Standard Python)"
            else:
                icon = "🟡"
                color = "#ff9800"
                status_text = status.gil_status.value.upper()
            
            html = f"<div style='border: 2px solid {color}; padding: 10px; border-radius: 5px;'>"
            html += f"<h3>{icon} GIL Status: {status_text}</h3>"
            html += f"<p><b>Python:</b> {status.python_version}</p>"
            html += f"<p><b>Build:</b> {status.build_info}</p>"
            
            if args.full:
                html += "<hr style='border: none; border-top: 1px solid #ddd; margin: 10px 0;'>"
                html += "<h4>📦 Package Compatibility</h4>"
                
                if status.free_threaded_packages:
                    html += f"<p><b>✅ Compatible:</b> {', '.join(status.free_threaded_packages[:3])}"
                    if len(status.free_threaded_packages) > 3:
                        html += f", +{len(status.free_threaded_packages)-3} more"
                    html += "</p>"
                
                if status.potentially_unsafe_packages:
                    html += f"<p><b>⚠️ Caution:</b> {', '.join(status.potentially_unsafe_packages[:3])}"
                    if len(status.potentially_unsafe_packages) > 3:
                        html += f", +{len(status.potentially_unsafe_packages)-3} more"
                    html += "</p>"
            
            html += "</div>"
            display(HTML(html))
            
        except Exception as e:
            display(HTML(f"❌ Error: {str(e)}"))


def load_ipython_extension(ipython):
    """Load the extension in IPython."""
    ipython.register_magics(AetherMagics)
    display(HTML(
        "<div style='background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 5px 0;'>"
        "✅ <b>Aether magics loaded</b><br/>"
        "Available: %%audit, %%profile_threads, %%free_threaded_check, %gil_status"
        "</div>"
    ))


def unload_ipython_extension(ipython):
    """Unload the extension."""
    pass
