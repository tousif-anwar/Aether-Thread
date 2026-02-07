"""
Command-line interface for Aether-Thread toolkit.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from aether_thread.analyzer import ThreadSafetyAnalyzer
from aether_thread.transformer import CodeTransformer


def analyze_file(filepath: str, verbose: bool = False) -> int:
    """
    Analyze a Python file for thread-safety issues.
    
    Returns:
        Exit code (0 if no critical issues, 1 otherwise)
    """
    try:
        with open(filepath, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1
    
    analyzer = ThreadSafetyAnalyzer()
    issues = analyzer.analyze_code(code, filename=filepath)
    summary = analyzer.get_summary()
    
    print(f"\nAnalyzing: {filepath}")
    print("=" * 60)
    
    if not issues:
        print("✓ No thread-safety issues found!")
    else:
        for issue in issues:
            severity_symbol = {
                'critical': '✗',
                'warning': '⚠',
                'info': 'ℹ'
            }.get(issue.severity, '•')
            
            location = ""
            if issue.line_number:
                location = f" [Line {issue.line_number}"
                if issue.column:
                    location += f", Col {issue.column}"
                location += "]"
            
            print(f"\n{severity_symbol} [{issue.severity.upper()}]{location}")
            print(f"  {issue.message}")
            
            if issue.suggestion and verbose:
                print(f"  💡 Suggestion: {issue.suggestion}")
    
    print("\nSummary:")
    print("-" * 60)
    print(f"Total Issues: {summary['total_issues']}")
    print(f"  Critical: {summary['critical']}")
    print(f"  Warnings: {summary['warnings']}")
    print(f"  Info: {summary['info']}")
    print(f"Global Writes: {summary['global_writes']}")
    print(f"Uses Threading: {summary['uses_threading']}")
    print(f"Thread-Safe: {summary['is_thread_safe']}")
    print("=" * 60)
    
    return 0 if summary['critical'] == 0 else 1


def transform_file(filepath: str, output: str = None, dry_run: bool = False) -> int:
    """
    Transform a Python file to add thread-safety.
    
    Returns:
        Exit code
    """
    try:
        with open(filepath, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1
    
    transformer = CodeTransformer()
    transformed_code, transformations = transformer.transform_code(code)
    
    print(f"\nTransforming: {filepath}")
    print("=" * 60)
    
    if not transformations:
        print("No transformations needed - code is already optimal!")
        return 0
    
    print("Transformations applied:")
    for i, trans in enumerate(transformations, 1):
        print(f"  {i}. {trans}")
    
    if dry_run:
        print("\n[DRY RUN] No files were modified")
        print("\nTransformed code preview:")
        print("-" * 60)
        print(transformed_code[:500] + "..." if len(transformed_code) > 500 else transformed_code)
    else:
        output_path = output or filepath
        try:
            with open(output_path, 'w') as f:
                f.write(transformed_code)
            print(f"\n✓ Transformed code written to: {output_path}")
        except Exception as e:
            print(f"Error writing file: {e}", file=sys.stderr)
            return 1
    
    print("=" * 60)
    return 0


def suggest_improvements(filepath: str) -> int:
    """
    Suggest improvements for a Python file.
    
    Returns:
        Exit code
    """
    try:
        with open(filepath, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1
    
    suggestions = CodeTransformer.suggest_improvements(code)
    
    print(f"\nSuggestions for: {filepath}")
    print("=" * 60)
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")
    
    print("=" * 60)
    return 0


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='aether-thread',
        description='Aether-Thread: Concurrency optimization toolkit for Python'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze Python code for thread-safety issues'
    )
    analyze_parser.add_argument('file', help='Python file to analyze')
    analyze_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed suggestions'
    )
    
    # Transform command
    transform_parser = subparsers.add_parser(
        'transform',
        help='Transform code to add thread-safety'
    )
    transform_parser.add_argument('file', help='Python file to transform')
    transform_parser.add_argument(
        '-o', '--output',
        help='Output file (default: overwrite input)'
    )
    transform_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    
    # Suggest command
    suggest_parser = subparsers.add_parser(
        'suggest',
        help='Suggest improvements for thread-safety'
    )
    suggest_parser.add_argument('file', help='Python file to analyze')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    if args.command == 'analyze':
        exit_code = analyze_file(args.file, verbose=args.verbose)
    elif args.command == 'transform':
        exit_code = transform_file(args.file, output=args.output, dry_run=args.dry_run)
    elif args.command == 'suggest':
        exit_code = suggest_improvements(args.file)
    else:
        parser.print_help()
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
