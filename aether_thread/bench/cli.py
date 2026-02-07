"""
CLI interface for aether-bench benchmarking suite.
"""

import argparse
import sys
from .runner import BenchmarkRunner


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog='aether-bench',
        description='Benchmark concurrent performance across configurations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aether-bench --all                    # Run all benchmarks
  aether-bench --list --ops 50000       # Benchmark lists with 50k ops
  aether-bench --dict --threads 8       # Benchmark dicts with 8 threads
        """
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all benchmarks'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='Run list benchmarks'
    )
    
    parser.add_argument(
        '--dict',
        action='store_true',
        help='Run dict benchmarks'
    )
    
    parser.add_argument(
        '--ops',
        type=int,
        default=10000,
        help='Number of operations per benchmark (default: 10000)'
    )
    
    parser.add_argument(
        '--threads',
        type=int,
        default=4,
        help='Number of threads for concurrent benchmarks (default: 4)'
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
    
    try:
        runner = BenchmarkRunner()
        
        if args.all:
            print(f"Running all benchmarks with {args.ops} operations...\n")
            runner.run_all_benchmarks(num_ops=args.ops)
        elif args.list:
            print(f"Running list benchmarks with {args.ops} operations...\n")
            runner.run_list_benchmarks(num_ops=args.ops)
            runner.benchmarker.print_results()
        elif args.dict:
            print(f"Running dict benchmarks with {args.ops} operations...\n")
            runner.run_dict_benchmarks(num_ops=args.ops)
            runner.benchmarker.print_results()
        else:
            print("Please specify --all, --list, or --dict")
            parser.print_help()
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
