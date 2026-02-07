"""
CLI interface for aether-audit static analyzer.
"""

import argparse
import sys
from pathlib import Path
from .scanner import StaticScanner


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog='aether-audit',
        description='Detect thread-safety issues in Python code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aether-audit .                  # Scan current directory
  aether-audit src/ --json        # Output as JSON
  aether-audit myapp --exclude    # Scan with custom exclusions
        """
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to scan (default: current directory)'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        default=['.venv', 'venv', '__pycache__', '.git'],
        help='Directories to exclude from scan'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with error code if any critical issues found'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    return parser


def main(argv=None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        return 1
    
    try:
        scanner = StaticScanner(exclude_dirs=args.exclude)
        results = scanner.scan(str(path))
        
        if args.json:
            import json
            data = {
                "summary": scanner.get_summary(),
                "findings": [
                    {
                        "file": f.file_path,
                        "line": f.line_number,
                        "type": f.issue_type,
                        "severity": f.severity,
                        "description": f.description,
                        "suggestion": f.suggestion,
                    }
                    for f in scanner.total_findings
                ]
            }
            print(json.dumps(data, indent=2))
        else:
            scanner.print_report()
        
        if args.strict and scanner.get_summary()['critical'] > 0:
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
