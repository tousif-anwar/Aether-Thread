"""
Example: Legacy code that needs thread-safety improvements.

This file demonstrates common patterns in legacy Python code that
need attention when transitioning to GIL-free environments.
"""

# Global variables without synchronization
counter = 0
user_cache = {}
request_queue = []


def increment_counter():
    """Unsafe: Modifies global without lock."""
    global counter
    counter += 1  # Not atomic!


def cache_user(user_id, user_data):
    """Unsafe: Dictionary access without lock."""
    global user_cache
    user_cache[user_id] = user_data


def process_request(request):
    """Unsafe: List operations without lock."""
    global request_queue
    request_queue.append(request)
    # Process first request
    if request_queue:
        first = request_queue.pop(0)
        return first


def complex_operation():
    """Unsafe: Multiple global operations."""
    global counter, user_cache
    
    # Multiple non-atomic operations
    counter += 1
    user_id = f"user_{counter}"
    user_cache[user_id] = {"id": user_id, "count": counter}
    
    return user_id


# Using eval/exec (dangerous)
def execute_code(code_str):
    """Very unsafe: Dynamic code execution."""
    return eval(code_str)


if __name__ == '__main__':
    print("This is legacy code that needs thread-safety improvements.")
    print("Run: aether-thread analyze examples/legacy_code.py")
