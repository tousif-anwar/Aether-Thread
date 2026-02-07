"""
Comprehensive example of aether-audit capabilities.

Demonstrates:
1. Global Variable Scanner - Detecting mutable globals
2. Race Condition Simulator - Finding race condition patterns  
3. Auto-Lock Injector - Suggesting synchronization fixes
"""

from aether.audit import audit_code, AuditReporter, RaceConditionDetector, AutoLockInjector


def example_unsafe_code():
    """Example 1: Unsafe code with global state and race conditions."""
    
    print("\n" + "="*80)
    print("EXAMPLE 1: UNSAFE CODE WITH MUTABLE GLOBALS AND RACE CONDITIONS")
    print("="*80)
    
    unsafe_code = """
# Thread-unsafe counter
counter = 0
shared_list = []

def increment_counter():
    '''Unsafe: Read-modify-write race condition'''
    global counter
    counter += 1  # NOT atomic!

def add_to_list(item):
    '''Unsafe: Global mutable list access'''
    global shared_list
    shared_list.append(item)

def check_and_increment():
    '''Unsafe: Check-then-act pattern'''
    global counter
    if counter < 100:  # Check happens here
        counter += 1   # Then modification - RACE WINDOW!
    return counter

class DataProcessor:
    # Class-level mutable state - shared across all instances!
    cache = {'processed': 0}
    results = []
    
    def process(self, data):
        self.cache['processed'] += 1  # RACE CONDITION
        self.results.append(data)     # THREAD-UNSAFE
        return data
"""
    
    # Run comprehensive audit
    report = audit_code(unsafe_code, "unsafe_example.py")
    print(report)
    
    # Detailed race condition analysis
    print("\nDETAILED RACE CONDITION ANALYSIS:")
    print("-" * 80)
    detector = RaceConditionDetector("unsafe_example.py")
    races = detector.detect(unsafe_code)
    for race in races:
        print(f"\n  Pattern: {race.pattern_type.upper()}")
        print(f"  Variable: {race.affected_variable}")
        print(f"  Severity: {race.severity}")
        print(f"  Issue: {race.description}")
        print(f"  Fix: {race.fix_suggestion}")


def example_with_fixes():
    """Example 2: Showing how fixes look."""
    
    print("\n" + "="*80)
    print("EXAMPLE 2: FIXED VERSION WITH PROPER SYNCHRONIZATION")
    print("="*80)
    
    fixed_code = """
from aether import atomic, ThreadSafeDict, ThreadSafeList

# Thread-safe counter wrapped in atomic function
counter = 0
shared_list = ThreadSafeList()  # Automatically synchronized

@atomic
def increment_counter():
    '''Safe: Atomic operation ensures mutual exclusion'''
    global counter
    counter += 1

def add_to_list(item):
    '''Safe: ThreadSafeList handles synchronization'''
    shared_list.append(item)

@atomic
def check_and_increment():
    '''Safe: Entire check-and-modify is atomic'''
    global counter
    if counter < 100:
        counter += 1
    return counter

class DataProcessor:
    def __init__(self):
        # Instance-specific state - not shared
        self.cache = ThreadSafeDict()        # Thread-safe dict
        self.results = ThreadSafeList()      # Thread-safe list
    
    @atomic
    def process(self, data):
        '''Safe: @atomic decorator ensures atomicity'''
        # Both operations execute without interference
        self.cache['processed'] = self.cache.get('processed', 0) + 1
        self.results.append(data)
        return data
"""
    
    # Audit the fixed version
    report = audit_code(fixed_code, "fixed_example.py")
    print(report)


def example_class_with_shared_state():
    """Example 3: Shared class attributes - a common pitfall."""
    
    print("\n" + "="*80)
    print("EXAMPLE 3: CLASS-LEVEL SHARED STATE PITFALL")
    print("="*80)
    
    class_example = """
class BankAccount:
    # MISTAKE: This is shared across ALL instances!
    transaction_log = []  # Every account shares this list
    
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
    
    def withdraw(self, amount):
        # When multiple threads create BankAccount instances,
        # they all write to the SAME transaction_log
        self.transaction_log.append(f"{self.owner} withdrew {amount}")
        self.balance -= amount

# Correct version:
class SafeBankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
        self.transaction_log = []  # Each instance has its own
    
    def withdraw(self, amount):
        self.transaction_log.append(f"{self.owner} withdrew {amount}")
        self.balance -= amount
"""
    
    report = audit_code(class_example, "bank_account.py")
    print(report)


def example_mutable_default_arguments():
    """Example 4: The infamous mutable default argument pitfall."""
    
    print("\n" + "="*80)
    print("EXAMPLE 4: MUTABLE DEFAULT ARGUMENTS")
    print("="*80)
    
    defaults_example = """
# WRONG: shared state across calls
def add_item(item, items=[]):  # [] is created ONCE at function definition
    items.append(item)
    return items

# First call: [1]
# Second call: [1, 2] - the [] was never recreated!
# In multithreading, this becomes a shared global state!

# CORRECT:
def add_item_safe(item, items=None):
    if items is None:
        items = []  # Fresh list each time
    items.append(item)
    return items

# For class methods:
class EventHandler:
    # WRONG: listeners shared across ALL instances
    def __init__(self, listeners=[]):
        self.listeners = listeners  # Bug!
    
    # CORRECT:
    def __init__(self, listeners=None):
        self.listeners = listeners or []  # Fresh list per instance
"""
    
    report = audit_code(defaults_example, "defaults.py")
    print(report)


def run_comprehensive_demo():
    """Run all demonstrations."""
    
    print("\n")
    print("█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "AETHER-AUDIT: COMPREHENSIVE THREAD-SAFETY DETECTION DEMO".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    print("\nThis demo showcases three complementary detection systems:")
    print("  1. Global Variable Scanner    - Finds mutable shared state")
    print("  2. Race Condition Simulator   - Detects unsafe patterns")
    print("  3. Auto-Lock Injector         - Suggests fixes\n")
    
    try:
        example_unsafe_code()
        example_with_fixes()
        example_class_with_shared_state()
        example_mutable_default_arguments()
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("""
The three detection systems work together to create a comprehensive audit toolkit:

🔴 SHARED STATE DETECTOR
   └─ Identifies global mutable variables, class attributes, and defaults
   └─ Severity: CRITICAL - causes silent data corruption

🟡 RACE CONDITION SIMULATOR
   └─ Detects check-then-act, read-modify-write, and compound operations
   └─ Severity: HIGH - causes non-deterministic failures

🟢 AUTO-LOCK INJECTOR
   └─ Recommends @atomic decorators, ThreadSafe wrappers, and explicit locks
   └─ Provides code examples for each fix strategy

USE CASES:
  • Legacy codebase migration to GIL-free Python 3.13+
  • Code review automation in CI/CD pipelines
  • Team training on thread-safety best practices
  • Finding hidden concurrency bugs before production

NEXT STEPS:
  from aether.audit import audit_code, audit_directory
  
  # Audit a single file
  report = audit_code(open("myfile.py").read(), "myfile.py")
  
  # Audit entire project
  report = audit_directory("/path/to/project")
""")
        
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/workspaces/Aether-Thread/src')
    
    run_comprehensive_demo()
