"""
Aether CLI: Command-line interface for thread-safety analysis and profiling.

Commands:
  aether check <path>        - Run thread-safety audit on code
  aether profile <script>    - Profile code to find saturation cliff
  aether status              - Check GIL and environment status
  aether scan <path>         - Deep scan for threading issues
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, List
import importlib.util

# Import aether modules
try:
    from aether.audit.analyzer import CodeAnalyzer
    from aether.audit.free_thread_detector import FreeThreadDetector
    from aether.profile import SaturationCliffProfiler
    from aether.check import GILStatusChecker
except ImportError:
    # Direct imports for development
    sys.path.insert(0, str(Path(__file__).parent))


class AetherCLI:
    """Command-line interface for Aether thread-safety toolkit."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description='Aether: Thread-safety analysis for Python',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  aether check mycode.py              # Find threading issues
  aether check src/                   # Audit entire directory
  aether profile benchmark.py         # Find saturation cliff
  aether status                       # Check GIL/environment
  aether scan . --all                 # Deep analysis with all checks
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Command to run')
        
        # CHECK command
        check_parser = subparsers.add_parser('check', help='Check code for thread-safety issues')
        check_parser.add_argument('path', help='File or directory to check')
        check_parser.add_argument('--free-threaded', action='store_true',
                                 help='Enable free-threaded Python checks')
        check_parser.add_argument('--verbose', '-v', action='store_true',
                                 help='Show detailed findings')
        
        # PROFILE command
        profile_parser = subparsers.add_parser('profile', help='Profile code to find saturation cliff')
        profile_parser.add_argument('script', help='Python script to profile')
        profile_parser.add_argument('--max-threads', type=int, default=32,
                                   help='Maximum threads to test (default: 32)')
        profile_parser.add_argument('--duration', type=float, default=5.0,
                                   help='Duration per run in seconds (default: 5.0)')
        
        # STATUS command
        status_parser = subparsers.add_parser('status', help='Check GIL and environment status')
        status_parser.add_argument('--verbose', '-v', action='store_true',
                                  help='Show detailed information')
        
        # SCAN command
        scan_parser = subparsers.add_parser('scan', help='Deep scan for threading issues')
        scan_parser.add_argument('path', help='Directory or file to scan')
        scan_parser.add_argument('--all', action='store_true',
                                help='Run all available checks')
        scan_parser.add_argument('--free-threaded', action='store_true',
                                help='Include free-threaded Python checks')
        
        return parser
    
    def run(self, args: Optional[List[str]] = None):
        """Run CLI with arguments."""
        parsed = self.parser.parse_args(args)
        
        if not parsed.command:
            self.parser.print_help()
            return 0
        
        try:
            if parsed.command == 'check':
                return self.check(parsed.path, parsed.free_threaded, parsed.verbose)
            elif parsed.command == 'profile':
                return self.profile(parsed.script, parsed.max_threads, parsed.duration)
            elif parsed.command == 'status':
                return self.status(parsed.verbose)
            elif parsed.command == 'scan':
                return self.scan(parsed.path, parsed.all, parsed.free_threaded)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1
    
    def check(self, path: str, free_threaded: bool = False, verbose: bool = False) -> int:
        """Check code for thread-safety issues."""
        print(f"\n📋 Checking: {path}")
        print("="*70)
        
        issues_found = False
        
        # Check file or directory
        paths_to_check = self._collect_python_files(path)
        
        if not paths_to_check:
            print(f"❌ No Python files found in {path}")
            return 1
        
        # Run standard audit
        print(f"\n🔍 Standard Thread-Safety Audit ({len(paths_to_check)} files):")
        for file_path in paths_to_check:
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                
                analyzer = CodeAnalyzer(file_path)
                findings = analyzer.analyze(code)
                
                if findings:
                    issues_found = True
                    print(f"\n  {file_path}:")
                    for finding in findings:
                        severity = "🔴" if finding.severity > 0.7 else "🟡"
                        print(f"    {severity} {finding.type}: {finding.description}")
                        if verbose:
                            print(f"       Line {finding.line_number}: {finding.code_snippet}")
            except Exception as e:
                print(f"  ⚠️ Error analyzing {file_path}: {e}")
        
        # Run free-threaded checks if requested
        if free_threaded:
            print(f"\n🟢 Free-Threaded Python Checks:")
            for file_path in paths_to_check:
                try:
                    with open(file_path, 'r') as f:
                        code = f.read()
                    
                    detector = FreeThreadDetector(file_path)
                    threats = detector.detect(code)
                    
                    if threats:
                        issues_found = True
                        print(f"\n  {file_path}:")
                        for threat in threats:
                            if threat.crash_risk:
                                icon = "🔴 CRASH RISK"
                            else:
                                icon = "🟡 SAFETY RISK"
                            print(f"    {icon}: {threat.description}")
                            print(f"       Fix: {threat.recommendation}")
                except Exception as e:
                    print(f"  ⚠️ Error checking {file_path}: {e}")
        
        print("\n" + "="*70)
        if issues_found:
            print("❌ Issues found - review above")
            return 1
        else:
            print("✅ No thread-safety issues found")
            return 0
    
    def profile(self, script: str, max_threads: int = 32, duration: float = 5.0) -> int:
        """Profile code to find saturation cliff."""
        if not os.path.exists(script):
            print(f"❌ Script not found: {script}")
            return 1
        
        print(f"\n⚡ Profiling: {script}")
        print("="*70)
        
        try:
            # Load and execute script to define workload
            spec = importlib.util.spec_from_file_location("workload_module", script)
            if spec.loader is None:
                print(f"❌ Cannot load: {script}")
                return 1
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for 'workload' function or 'benchmark' function
            workload_fn = None
            if hasattr(module, 'workload'):
                workload_fn = module.workload
            elif hasattr(module, 'benchmark'):
                workload_fn = module.benchmark
            else:
                print("❌ Script must define 'workload()' or 'benchmark()' function")
                return 1
            
            # Run profiler
            print(f"Running exponential thread profile (max={max_threads}, duration={duration}s)...\n")
            
            profiler = SaturationCliffProfiler(
                workload_fn,
                duration_per_run=duration,
                max_threads=max_threads
            )
            analysis = profiler.profile()
            
            # Display results
            print("\n" + analysis.plot_ascii_chart())
            print("\n" + "="*70)
            print(f"📊 Results:")
            print(f"  Optimal threads: {analysis.optimal_threads}")
            print(f"  Saturation cliff: {analysis.cliff_threads} threads")
            print(f"  Cliff severity: {analysis.cliff_severity*100:.1f}%")
            print(f"  Recommendation: Use {analysis.optimal_threads} threads")
            
            return 0
        except Exception as e:
            print(f"❌ Error profiling: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    def status(self, verbose: bool = False) -> int:
        """Check GIL and environment status."""
        checker = GILStatusChecker()
        checker.print_status()
        return 0
    
    def scan(self, path: str, all_checks: bool = False, free_threaded: bool = False) -> int:
        """Deep scan for threading issues."""
        print(f"\n🔎 Deep Scan: {path}")
        print("="*70)
        
        # Collect files
        files = self._collect_python_files(path)
        if not files:
            print(f"❌ No Python files found")
            return 1
        
        print(f"Found {len(files)} Python files\n")
        
        # Run checks
        if all_checks or not free_threaded:
            print("Running thread-safety audit...")
            self.check(path, free_threaded=False, verbose=True)
        
        if all_checks or free_threaded:
            print("Running free-threaded checks...")
            self.check(path, free_threaded=True, verbose=True)
        
        return 0
    
    def _collect_python_files(self, path: str) -> List[str]:
        """Collect all Python files from path."""
        p = Path(path)
        if p.is_file():
            return [str(p)] if p.suffix == '.py' else []
        
        if p.is_dir():
            return sorted(str(f) for f in p.rglob('*.py') 
                         if not any(part.startswith('.') for part in f.parts)
                         and not any(part in ('__pycache__', 'venv', '.venv') for part in f.parts))
        
        return []


def main(args: Optional[List[str]] = None):
    """Main entry point."""
    cli = AetherCLI()
    return cli.run(args)


if __name__ == '__main__':
    sys.exit(main())
