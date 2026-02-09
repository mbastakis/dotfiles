// Rust test file with intentional format/lint issues
use std::collections::HashMap;

use std::fs::File;
use std::io::{self, Read, Write};

// Unused import
use std::path::PathBuf;

#[derive(Debug, Clone)]
struct User {
    name: String,
    age: u32,
    email: Option<String>,
}

impl User {
    fn new(name: String, age: u32) -> Self {
        User {
            name,
            age,
            email: None,
        }
    }

    // Very long line
    fn with_email(name: String, age: u32, email: String) -> Self {
        User {
            name: name.clone(),
            age: age,
            email: Some(email),
        }
    }
}

// Unused function
fn unused_helper(x: i32) -> i32 {
    x * 2
}

fn process_users(users: &Vec<User>) -> Vec<String> {
    let mut result = Vec::new();
    for user in users {
        // Unnecessary clone
        let name = user.name.clone();
        result.push(name)
    }
    return result;
}

fn main() {
    let mut users: Vec<User> = vec![];

    users.push(User::new("John".to_string(), 30));
    users.push(User::new("Jane".to_string(), 25));

    // Inconsistent spacing
    let names = process_users(&users);

    // Unused variable
    let unused = 42;

    for name in names {
        println!("{}", name)
    }

    // Unwrap without error handling
    let file = File::open("test.txt").unwrap();

    // Missing error handling
    let mut map = HashMap::new();
    map.insert("key1", "value1");
    map.insert("key2", "value2");

    match map.get("key1") {
        Some(v) => println!("Found: {}", v),
        None => println!("Not found"),
    }
}
