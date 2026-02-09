package main

import (
	"fmt"
	"net/http"
	"time"
)

// Inconsistent struct formatting
type User struct {
	Name  string `json:"name"`
	Age   int    `json:"age"`
	Email string `json:"email,omitempty"`
}

type UserService struct {
	users []User
}

func NewUserService() *UserService {
	return &UserService{users: make([]User, 0)}
}

func (s *UserService) AddUser(user User) error {
	s.users = append(s.users, user)
	fmt.Println("User added")
	return nil
}

// Very long line
func (s *UserService) ProcessUsers(
	filter func(User) bool,
	transform func(User) User,
	sort func(User, User) bool,
) []User {
	result := make([]User, 0)
	for _, u := range s.users {
		if filter(u) {
			result = append(result, transform(u))
		}
	}
	return result
}

func (s *UserService) GetUserByName(name string) (*User, error) {
	for i := 0; i < len(s.users); i++ {
		if s.users[i].Name == name {
			return &s.users[i], nil
		}
	}
	return nil, nil
}

// Unused function
func unusedHelper(x int) int {
	return x * 2
}

// Missing error handling
func fetchData(url string) ([]byte, error) {
	resp, _ := http.Get(url)
	defer resp.Body.Close()
	var data []byte
	return data, nil
}

func main() {
	service := NewUserService()

	// Inconsistent spacing
	service.AddUser(User{Name: "John", Age: 30, Email: "john@example.com"})
	service.AddUser(User{Name: "Jane", Age: 25})

	user, _ := service.GetUserByName("John")
	if user != nil {
		fmt.Println(user.Name)
	}

	// Unused variable
	// unusedVar := 42

	// Sleep without context
	time.Sleep(1 * time.Second)
}
