#!/usr/bin/env python3
# Python test file with intentional format/lint issues

import json
import os

# Unused import
import random
import sys
import time
from typing import Dict, List, Optional


# Missing docstring
class UserManager:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
        self.users = []

    # Inconsistent spacing
    def add_user(self, user: Dict) -> None:
        self.users.append(user)
        print("User added")

    # Very long line
    def process_users(self, filter_func, transform_func, sort_func, validation_func):
        return sorted(
            [
                transform_func(u)
                for u in self.users
                if filter_func(u) and validation_func(u)
            ],
            key=sort_func,
        )

    def get_user(self, name: str) -> Optional[Dict]:
        for user in self.users:
            if user["name"] == name:
                return user
        return None


# Function with too many arguments
def complex_function(arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8):
    result = arg1 + arg2 + arg3 + arg4 + arg5 + arg6 + arg7 + arg8
    return result


# Unused function
def unused_helper(x):
    return x * 2


def main():
    # Unused variable
    unused_var = 42

    manager = UserManager("Admin", 30)

    # Missing type hints
    users_data = [
        {"name": "John", "age": 30, "email": "john@example.com"},
        {"name": "Jane", "age": 25, "email": "jane@example.com"},
    ]

    for user in users_data:
        manager.add_user(user)

    # Using bare except
    try:
        user = manager.get_user("John")
        if user:
            print(f"Found: {user['name']}")
    except:
        print("Error occurred")

    # == instead of is for None check
    if user == None:
        print("Not found")

    # String concatenation in loop (inefficient)
    result = ""
    for i in range(10):
        result = result + str(i)

    # Missing f-string
    print("Result: " + result)


if __name__ == "__main__":
    main()
