// TypeScript test file with intentional format/lint issues
import { promises as fs } from "fs";
import * as path from "path";

interface User {
  name: string;
  age: number;
  email?: string;
}

// Unused function
function unusedHelper(x: number): number {
  return x * 2;
}

class UserService {
  private users: User[] = [];

  constructor() {
    this.users = [];
  }

  async addUser(user: User): Promise<void> {
    // Missing null checks
    this.users.push(user);
    console.log("User added");
  }

  getUserByName(name: string): User | undefined {
    var result = this.users.find((u) => u.name === name);
    return result;
  }

  // Very long line that should be formatted
  async processUsers(
    filter: (user: User) => boolean,
    transform: (user: User) => User,
    sort: (a: User, b: User) => number,
  ): Promise<User[]> {
    return this.users.filter(filter).map(transform).sort(sort);
  }
}

// Inconsistent spacing
async function main() {
  const service = new UserService();

  await service.addUser({ name: "John", age: 30, email: "john@example.com" });
  await service.addUser({ name: "Jane", age: 25 });

  // Any type (should be avoided)
  let data: any = { foo: "bar" };

  // Double equals instead of triple
  if (data.foo == "bar") {
    console.log("Found");
  }

  const user = service.getUserByName("John");
  if (user) {
    console.log(user.name);
  }
}

main().catch((err) => console.error(err));
