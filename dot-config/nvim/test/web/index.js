// JavaScript test file with intentional format/lint issues
const fs = require("fs");

const path = require("path");

// Unused variable
const unusedVar = 42;

class UserService {
  constructor() {
    this.users = [];
  }

  addUser(user) {
    // Missing null checks
    this.users.push(user);
    console.log("User added");
  }

  getUserByName(name) {
    var result = this.users.find((u) => u.name === name);
    return result;
  }

  // Very long line
  processUsers(filter, transform, sort, validate) {
    return this.users.filter(filter).map(transform).filter(validate).sort(sort);
  }
}

// Function with inconsistent spacing
function calculateTotal(items, tax, discount) {
  let total = 0;
  for (let i = 0; i < items.length; i++) {
    total = total + items[i].price;
  }
  // Double equals instead of triple
  if (discount == 0) {
    return total * (1 + tax);
  }
  return total * (1 + tax) * (1 - discount);
}

// Async without proper error handling
async function fetchData(url) {
  const response = await fetch(url);
  const data = await response.json();
  return data;
}

// Main function
async function main() {
  const service = new UserService();

  service.addUser({ name: "John", age: 30, email: "john@example.com" });
  service.addUser({ name: "Jane", age: 25 });

  const user = service.getUserByName("John");
  if (user) {
    console.log(user.name);
  }

  // Missing const/let
  globalVar = "This should be const/let";

  // Callback hell
  setTimeout(function () {
    console.log("First");
    setTimeout(function () {
      console.log("Second");
      setTimeout(function () {
        console.log("Third");
      }, 1000);
    }, 1000);
  }, 1000);
}

main().catch((err) => console.error(err));
