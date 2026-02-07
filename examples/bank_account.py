"""
Example: BankAccount with @atomic decorator and contention monitoring.

This example demonstrates:
1. Using @atomic to protect shared state
2. Contention monitoring to identify hot spots
3. Thread-safe concurrent operations
"""

import threading
import time
from aether import atomic, synchronized, ThreadSafeDict
from aether.monitor import get_monitor


# ============================================================================
# EXAMPLE 1: Bank Account with @atomic decorator
# ============================================================================

class BankAccount:
    """Bank account with thread-safe operations using @atomic decorator."""
    
    def __init__(self, account_id: str, initial_balance: float = 0):
        self.account_id = account_id
        self.balance = initial_balance
        self.transaction_count = 0
    
    @atomic
    def deposit(self, amount: float) -> float:
        """Deposit money into account (atomic operation)."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        # Simulate some processing time
        time.sleep(0.001)
        
        self.balance += amount
        self.transaction_count += 1
        return self.balance
    
    @atomic
    def withdraw(self, amount: float) -> float:
        """Withdraw money from account (atomic operation)."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        
        # Simulate some processing time
        time.sleep(0.001)
        
        self.balance -= amount
        self.transaction_count += 1
        return self.balance
    
    @atomic
    def get_balance(self) -> float:
        """Get current balance."""
        return self.balance
    
    @atomic
    def transfer(self, recipient: "BankAccount", amount: float) -> bool:
        """Transfer money to another account."""
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        if amount > self.balance:
            return False
        
        self.balance -= amount
        self.transaction_count += 1
        
        # Simulate network delay
        time.sleep(0.002)
        
        recipient.balance += amount
        recipient.transaction_count += 1
        return True


# ============================================================================
# EXAMPLE 2: Bank System with multiple accounts
# ============================================================================

class BankingSystem:
    """Bank system managing multiple accounts with concurrent operations."""
    
    def __init__(self):
        self.accounts: ThreadSafeDict = ThreadSafeDict()
    
    def create_account(self, account_id: str, initial_balance: float = 0) -> BankAccount:
        """Create a new bank account."""
        account = BankAccount(account_id, initial_balance)
        self.accounts[account_id] = account
        return account
    
    def get_account(self, account_id: str) -> BankAccount:
        """Get an account by ID."""
        return self.accounts[account_id]


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demo_atomic_decorator():
    """Demonstrate @atomic decorator for thread safety."""
    print("\n" + "="*80)
    print("DEMO 1: @atomic Decorator - Bank Account")
    print("="*80)
    
    account = BankAccount("ACC001", initial_balance=1000)
    print(f"Initial balance: ${account.get_balance():.2f}")
    
    # Simulate concurrent deposits from multiple threads
    def simulate_customer_deposits(num_deposits: int):
        for _ in range(num_deposits):
            try:
                account.deposit(100)
            except Exception as e:
                print(f"Error: {e}")
    
    threads = []
    for i in range(5):
        t = threading.Thread(
            target=simulate_customer_deposits,
            args=(10,),
            name=f"Depositor-{i+1}"
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    final_balance = account.get_balance()
    expected_balance = 1000 + (5 * 10 * 100)  # 5 threads, 10 deposits each, $100 per deposit
    
    print(f"\nFinal balance: ${final_balance:.2f}")
    print(f"Expected balance: ${expected_balance:.2f}")
    print(f"Transactions processed: {account.transaction_count}")
    print(f"✓ Account is thread-safe: {final_balance == expected_balance}")


def demo_contention_monitoring():
    """Demonstrate contention monitoring to identify hot locks."""
    print("\n" + "="*80)
    print("DEMO 2: Contention Monitoring")
    print("="*80)
    
    # Enable contention monitoring
    monitor = get_monitor()
    monitor.enable()
    
    class CachedService:
        """Service with a hot cache lock."""
        
        def __init__(self):
            self.cache = {}
        
        @atomic
        def get_or_compute(self, key: str, compute_fn) -> any:
            """Get value from cache or compute it."""
            if key in self.cache:
                return self.cache[key]
            
            # Compute value (hot spot - lots of contention here)
            time.sleep(0.01)
            value = compute_fn(key)
            self.cache[key] = value
            return value
    
    service = CachedService()
    
    def worker_thread(worker_id: int):
        """Worker that calls the cached service."""
        for i in range(50):
            key = f"data_{i % 5}"  # Only 5 different keys
            value = service.get_or_compute(key, lambda k: f"computed_{k}")
            time.sleep(0.001)
    
    # Spawn worker threads
    threads = [
        threading.Thread(target=worker_thread, args=(i,))
        for i in range(5)
    ]
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    # Print contention report
    print("\nLock Contention Analysis:")
    print("-" * 80)
    stats = monitor.get_stats()
    if stats.metrics:
        for lock_name, metrics in stats.metrics.items():
            print(f"\nLock: {lock_name}")
            print(f"  Total acquisitions: {metrics.total_acquisitions}")
            print(f"  Contention count: {metrics.contention_count}")
            print(f"  Contention rate: {metrics.contention_rate:.1f}%")
            print(f"  Avg wait time: {metrics.average_wait_time * 1000:.2f}ms")
            print(f"  Contention level: {metrics.contention_level.value.upper()}")
    
    monitor.print_report()
    monitor.disable()


def demo_concurrent_transfers():
    """Demonstrate concurrent transfers between accounts."""
    print("\n" + "="*80)
    print("DEMO 3: Concurrent Account Transfers")
    print("="*80)
    
    # Create bank system
    bank = BankingSystem()
    alice = bank.create_account("ALICE", 1000)
    bob = bank.create_account("BOB", 1000)
    charlie = bank.create_account("CHARLIE", 1000)
    
    print(f"Initial state:")
    print(f"  Alice: ${alice.get_balance():.2f}")
    print(f"  Bob:   ${bob.get_balance():.2f}")
    print(f"  Charlie: ${charlie.get_balance():.2f}")
    
    def transfer_worker(from_account: BankAccount, to_account: BankAccount, amount: float, transfers: int):
        """Worker that makes transfers."""
        for _ in range(transfers):
            try:
                from_account.transfer(to_account, amount)
            except ValueError:
                pass  # Insufficient funds
            time.sleep(0.001)
    
    # Create concurrent transfers
    threads = [
        threading.Thread(target=transfer_worker, args=(alice, bob, 10, 20)),
        threading.Thread(target=transfer_worker, args=(bob, charlie, 10, 20)),
        threading.Thread(target=transfer_worker, args=(charlie, alice, 10, 20)),
    ]
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    alice_balance = alice.get_balance()
    bob_balance = bob.get_balance()
    charlie_balance = charlie.get_balance()
    total = alice_balance + bob_balance + charlie_balance
    
    print(f"\nFinal state:")
    print(f"  Alice: ${alice_balance:.2f}")
    print(f"  Bob:   ${bob_balance:.2f}")
    print(f"  Charlie: ${charlie_balance:.2f}")
    print(f"  Total: ${total:.2f} (should be $3000.00)")
    print(f"✓ Money is conserved: {total == 3000}")


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "AETHER-THREAD: @atomic Decorator Examples" + " "*22 + "║")
    print("╚" + "="*78 + "╝")
    
    # Run demonstrations
    demo_atomic_decorator()
    demo_concurrent_transfers()
    demo_contention_monitoring()
    
    print("\n" + "="*80)
    print("✓ All examples completed successfully!")
    print("="*80 + "\n")
