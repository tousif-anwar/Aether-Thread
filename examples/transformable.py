"""
Example code that can benefit from transformations.
"""

global shared_value
shared_value = 100

def modify_shared():
    global shared_value
    shared_value = shared_value + 1
    return shared_value

def another_modifier():
    global shared_value
    shared_value = shared_value * 2
    return shared_value
