# Bubbletea TUI Framework Documentation
*Comprehensive guide for LLM agents implementing Terminal User Interfaces in Go*

## Table of Contents
1. [Executive Summary & Quick Reference](#executive-summary--quick-reference)
2. [Core Architecture Deep Dive](#core-architecture-deep-dive)
3. [Component Library Reference](#component-library-reference)
4. [Practical Code Examples](#practical-code-examples)
5. [Best Practices & Patterns](#best-practices--patterns)
6. [Common Entry Points & Templates](#common-entry-points--templates)
7. [LLM-Optimized Reference](#llm-optimized-reference)

---

## Executive Summary & Quick Reference

### What is Bubbletea?
Bubbletea is a Go framework for building interactive terminal user interfaces (TUIs), based on The Elm Architecture. It provides a clean, functional approach to creating both simple and complex terminal applications.

### Core Ecosystem
- **Bubbletea**: Core TUI framework (github.com/charmbracelet/bubbletea)
- **Bubbles**: UI components library (github.com/charmbracelet/bubbles)  
- **Lip Gloss**: Styling and layout (github.com/charmbracelet/lipgloss)

### Essential Imports
```go
package main

import (
    "fmt"
    "log"
    "os"
    
    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/lipgloss"
    "github.com/charmbracelet/bubbles/list"
    "github.com/charmbracelet/bubbles/textinput"
    "github.com/charmbracelet/bubbles/table"
    "github.com/charmbracelet/bubbles/spinner"
)
```

### Quick Start Template
```go
package main

import (
    "fmt"
    tea "github.com/charmbracelet/bubbletea"
)

type model struct {
    // Application state goes here
}

func (m model) Init() tea.Cmd {
    // Initial command (can be nil)
    return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        if msg.String() == "q" {
            return m, tea.Quit
        }
    }
    return m, nil
}

func (m model) View() string {
    return "Hello, World!\nPress 'q' to quit."
}

func main() {
    p := tea.NewProgram(model{})
    if _, err := p.Run(); err != nil {
        fmt.Printf("Error: %v", err)
        os.Exit(1)
    }
}
```

### Key Concepts Summary
- **Model**: Holds application state
- **Init()**: Returns initial command
- **Update()**: Handles events, returns updated model and command
- **View()**: Renders UI as string
- **Command**: Async function that returns a message
- **Message**: Event that triggers state updates

---

## Core Architecture Deep Dive

### The Elm Architecture Pattern
Bubbletea implements the Model-Update-View (MVU) architecture:

```
User Input → Message → Update → Model → View → Render
     ↑                                           ↓
     ←←←←←←←←←←← Command ←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

### Model Definition
The model represents your application's state. It can be any Go type but typically a struct:

```go
type model struct {
    // State fields
    counter    int
    message    string
    loading    bool
    error      error
    
    // UI component states
    list       list.Model
    textInput  textinput.Model
    table      table.Model
}
```

### Init() Method
Returns an initial command to run when the application starts:

```go
func (m model) Init() tea.Cmd {
    // Return nil for no initial command
    return nil
    
    // Return a command to run immediately
    return tea.Batch(
        textinput.Blink,
        spinner.Tick,
        fetchDataCmd(),
    )
}
```

### Update() Method
Core of the application logic - handles all events and state transitions:

```go
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    
    // Handle keyboard input
    case tea.KeyMsg:
        switch msg.String() {
        case "ctrl+c", "q":
            return m, tea.Quit
        case "enter":
            return m, processEnterCmd()
        }
    
    // Handle window resize
    case tea.WindowSizeMsg:
        m.width = msg.Width
        m.height = msg.Height
        
    // Handle custom messages
    case dataLoadedMsg:
        m.data = msg.data
        m.loading = false
        
    case errorMsg:
        m.error = msg.err
        m.loading = false
    }
    
    // Update child components
    var cmd tea.Cmd
    m.list, cmd = m.list.Update(msg)
    
    return m, cmd
}
```

### View() Method
Renders the current state as a string:

```go
func (m model) View() string {
    if m.loading {
        return "Loading..."
    }
    
    if m.error != nil {
        return fmt.Sprintf("Error: %v", m.error)
    }
    
    // Build UI with components
    content := lipgloss.JoinVertical(
        lipgloss.Left,
        m.headerView(),
        m.list.View(),
        m.footerView(),
    )
    
    return lipgloss.Place(
        m.width, m.height,
        lipgloss.Center, lipgloss.Center,
        content,
    )
}
```

### Commands and Async Operations
Commands handle I/O operations and async tasks:

```go
// Command type definition
type Cmd func() Msg

// Custom message types
type dataLoadedMsg struct{ data []string }
type errorMsg struct{ err error }

// Command function
func fetchDataCmd() tea.Cmd {
    return func() tea.Msg {
        // Simulate API call
        time.Sleep(2 * time.Second)
        
        data, err := fetchFromAPI()
        if err != nil {
            return errorMsg{err}
        }
        
        return dataLoadedMsg{data}
    }
}

// Using commands in Update
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        if msg.String() == "r" {
            m.loading = true
            return m, fetchDataCmd()
        }
    }
    return m, nil
}
```

### Message Types
Define custom messages for different events:

```go
// Network messages
type httpResponseMsg struct {
    status int
    body   string
}

type httpErrorMsg struct {
    err error
}

// User action messages  
type itemSelectedMsg struct {
    index int
    item  string
}

type formSubmittedMsg struct {
    name  string
    email string
}

// System messages
type timerTickMsg time.Time
type fileLoadedMsg struct {
    filename string
    content  []byte
}
```

---

## Component Library Reference

### 1. Text Input Component
Single-line text entry with features like unicode support, pasting, and scrolling.

```go
import "github.com/charmbracelet/bubbles/textinput"

type model struct {
    textInput textinput.Model
}

func initialModel() model {
    ti := textinput.New()
    ti.Placeholder = "Enter text here..."
    ti.Focus()
    ti.CharLimit = 156
    ti.Width = 20
    
    return model{textInput: ti}
}

func (m model) Init() tea.Cmd {
    return textinput.Blink
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmd tea.Cmd
    
    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.Type {
        case tea.KeyEnter:
            // Process input
            value := m.textInput.Value()
            // Do something with value
            return m, nil
        case tea.KeyEsc:
            return m, tea.Quit
        }
    }
    
    m.textInput, cmd = m.textInput.Update(msg)
    return m, cmd
}

func (m model) View() string {
    return fmt.Sprintf(
        "Enter your input:\n\n%s\n\n(esc to quit)",
        m.textInput.View(),
    )
}
```

### 2. Text Area Component
Multi-line text input with vertical scrolling:

```go
import "github.com/charmbracelet/bubbles/textarea"

type model struct {
    textarea textarea.Model
}

func initialModel() model {
    ta := textarea.New()
    ta.Placeholder = "Enter your text..."
    ta.Focus()
    ta.SetWidth(50)
    ta.SetHeight(10)
    
    return model{textarea: ta}
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmd tea.Cmd
    m.textarea, cmd = m.textarea.Update(msg)
    return m, cmd
}
```

### 3. List Component
Interactive list with pagination, filtering, and selection:

```go
import "github.com/charmbracelet/bubbles/list"

type item string
func (i item) FilterValue() string { return string(i) }

type model struct {
    list list.Model
}

func initialModel() model {
    items := []list.Item{
        item("Item 1"),
        item("Item 2"), 
        item("Item 3"),
    }
    
    l := list.New(items, list.NewDefaultDelegate(), 20, 14)
    l.Title = "My List"
    
    return model{list: l}
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        if msg.String() == "enter" {
            selected := m.list.SelectedItem()
            // Process selected item
        }
    }
    
    var cmd tea.Cmd
    m.list, cmd = m.list.Update(msg)
    return m, cmd
}

func (m model) View() string {
    return m.list.View()
}
```

### 4. Table Component
Tabular data display with sorting and navigation:

```go
import "github.com/charmbracelet/bubbles/table"

func createTable() table.Model {
    columns := []table.Column{
        {Title: "Name", Width: 20},
        {Title: "Age", Width: 10},
        {Title: "City", Width: 15},
    }
    
    rows := []table.Row{
        {"John", "25", "New York"},
        {"Jane", "30", "Boston"},
        {"Bob", "35", "Chicago"},
    }
    
    t := table.New(
        table.WithColumns(columns),
        table.WithRows(rows),
        table.WithFocused(true),
        table.WithHeight(7),
    )
    
    return t
}
```

### 5. Spinner Component
Loading spinner for indicating background operations:

```go
import "github.com/charmbracelet/bubbles/spinner"

type model struct {
    spinner spinner.Model
    loading bool
}

func initialModel() model {
    s := spinner.New()
    s.Spinner = spinner.Dot
    s.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("205"))
    
    return model{
        spinner: s,
        loading: true,
    }
}

func (m model) Init() tea.Cmd {
    return m.spinner.Tick
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmd tea.Cmd
    
    switch msg := msg.(type) {
    case spinner.TickMsg:
        m.spinner, cmd = m.spinner.Update(msg)
        return m, cmd
    }
    
    return m, nil
}

func (m model) View() string {
    if m.loading {
        return fmt.Sprintf("%s Loading...", m.spinner.View())
    }
    return "Done!"
}
```

### 6. Progress Bar Component
Visual progress indication:

```go
import "github.com/charmbracelet/bubbles/progress"

type model struct {
    progress progress.Model
}

func initialModel() model {
    return model{
        progress: progress.New(progress.WithDefaultGradient()),
    }
}

func (m model) View() string {
    return fmt.Sprintf(
        "Progress: %s\n%s",
        m.progress.View(),
        "Press any key to continue...",
    )
}

// Update progress
func (m model) updateProgress(percent float64) model {
    cmd := m.progress.SetPercent(percent)
    // Handle the command appropriately
    return m
}
```

### 7. Viewport Component
Scrollable content viewer:

```go
import "github.com/charmbracelet/bubbles/viewport"

type model struct {
    viewport viewport.Model
    content  string
}

func initialModel() model {
    vp := viewport.New(80, 20)
    vp.SetContent("Very long content that needs scrolling...")
    
    return model{
        viewport: vp,
        content:  "Long content here...",
    }
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmd tea.Cmd
    m.viewport, cmd = m.viewport.Update(msg)
    return m, cmd
}
```

### 8. Paginator Component
Page navigation for large datasets:

```go
import "github.com/charmbracelet/bubbles/paginator"

type model struct {
    paginator paginator.Model
    items     []string
}

func initialModel() model {
    items := make([]string, 100) // Large dataset
    for i := range items {
        items[i] = fmt.Sprintf("Item %d", i+1)
    }
    
    p := paginator.New()
    p.Type = paginator.Dots
    p.PerPage = 10
    p.SetTotalPages(len(items) / 10)
    
    return model{
        paginator: p,
        items:     items,
    }
}
```

### 9. File Picker Component
Navigate and select files from filesystem:

```go
import "github.com/charmbracelet/bubbles/filepicker"

type model struct {
    filepicker filepicker.Model
}

func initialModel() model {
    fp := filepicker.New()
    fp.AllowedTypes = []string{".md", ".txt", ".go"}
    fp.CurrentDirectory, _ = os.UserHomeDir()
    
    return model{filepicker: fp}
}
```

### 10. Timer & Stopwatch Components
Time-based components:

```go
import (
    "github.com/charmbracelet/bubbles/timer"
    "github.com/charmbracelet/bubbles/stopwatch"
)

type model struct {
    timer     timer.Model
    stopwatch stopwatch.Model
}

func initialModel() model {
    return model{
        timer:     timer.NewWithInterval(30*time.Second, time.Second),
        stopwatch: stopwatch.NewWithInterval(time.Millisecond * 100),
    }
}
```

### Lip Gloss Styling
CSS-like styling for terminal interfaces:

```go
import "github.com/charmbracelet/lipgloss"

// Define styles
var (
    titleStyle = lipgloss.NewStyle().
        Foreground(lipgloss.Color("#FFFDF5")).
        Background(lipgloss.Color("#25A065")).
        Padding(0, 1)
        
    boxStyle = lipgloss.NewStyle().
        Border(lipgloss.RoundedBorder()).
        BorderForeground(lipgloss.Color("62")).
        Padding(1, 2)
        
    selectedStyle = lipgloss.NewStyle().
        Foreground(lipgloss.Color("170")).
        Bold(true)
)

// Apply styles
func (m model) View() string {
    title := titleStyle.Render("My Application")
    content := boxStyle.Render("Content goes here")
    
    return lipgloss.JoinVertical(
        lipgloss.Left,
        title,
        content,
    )
}
```

---

## Practical Code Examples

### Beginner Example: Simple List Selection
Complete example from the bubbletea repository:

```go
package main

import (
    "fmt"
    "io"
    "os"
    "strings"

    "github.com/charmbracelet/bubbles/list"
    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/lipgloss"
)

const listHeight = 14

var (
    titleStyle        = lipgloss.NewStyle().MarginLeft(2)
    itemStyle         = lipgloss.NewStyle().PaddingLeft(4)
    selectedItemStyle = lipgloss.NewStyle().PaddingLeft(2).Foreground(lipgloss.Color("170"))
    paginationStyle   = list.DefaultStyles().PaginationStyle.PaddingLeft(4)
    helpStyle         = list.DefaultStyles().HelpStyle.PaddingLeft(4).PaddingBottom(1)
    quitTextStyle     = lipgloss.NewStyle().Margin(1, 0, 2, 4)
)

type item string

func (i item) FilterValue() string { return "" }

type itemDelegate struct{}

func (d itemDelegate) Height() int                             { return 1 }
func (d itemDelegate) Spacing() int                            { return 0 }
func (d itemDelegate) Update(_ tea.Msg, _ *list.Model) tea.Cmd { return nil }
func (d itemDelegate) Render(w io.Writer, m list.Model, index int, listItem list.Item) {
    i, ok := listItem.(item)
    if !ok {
        return
    }

    str := fmt.Sprintf("%d. %s", index+1, i)

    fn := itemStyle.Render
    if index == m.Index() {
        fn = func(s ...string) string {
            return selectedItemStyle.Render("> " + strings.Join(s, " "))
        }
    }

    fmt.Fprint(w, fn(str))
}

type model struct {
    list   list.Model
    choice string
    quitting bool
}

func (m model) Init() tea.Cmd {
    return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.list.SetWidth(msg.Width)
        return m, nil

    case tea.KeyMsg:
        switch keypress := msg.String(); keypress {
        case "q", "ctrl+c":
            m.quitting = true
            return m, tea.Quit

        case "enter":
            i, ok := m.list.SelectedItem().(item)
            if ok {
                m.choice = string(i)
            }
            return m, tea.Quit
        }
    }

    var cmd tea.Cmd
    m.list, cmd = m.list.Update(msg)
    return m, cmd
}

func (m model) View() string {
    if m.choice != "" {
        return quitTextStyle.Render(fmt.Sprintf("%s? Sounds good to me.", m.choice))
    }
    if m.quitting {
        return quitTextStyle.Render("Not hungry? That's cool.")
    }
    return "\n" + m.list.View()
}

func main() {
    items := []list.Item{
        item("Ramen"),
        item("Tomato Soup"),
        item("Hamburgers"),
        item("Cheeseburgers"),
        item("Currywurst"),
        item("Okonomiyaki"),
        item("Pasta"),
        item("Fillet mignon"),
        item("Caviar"),
        item("Just wine"),
    }

    const defaultWidth = 20

    l := list.New(items, itemDelegate{}, defaultWidth, listHeight)
    l.Title = "What do you want for dinner?"
    l.SetShowStatusBar(false)
    l.SetFilteringEnabled(false)
    l.Styles.Title = titleStyle
    l.Styles.PaginationStyle = paginationStyle
    l.Styles.HelpStyle = helpStyle

    m := model{list: l}

    if _, err := tea.NewProgram(m).Run(); err != nil {
        fmt.Println("Error running program:", err)
        os.Exit(1)
    }
}
```

### Intermediate Example: Text Input with Validation
```go
package main

import (
    "fmt"
    "log"

    "github.com/charmbracelet/bubbles/textinput"
    tea "github.com/charmbracelet/bubbletea"
)

func main() {
    p := tea.NewProgram(initialModel())
    if _, err := p.Run(); err != nil {
        log.Fatal(err)
    }
}

type (
    errMsg error
)

type model struct {
    textInput textinput.Model
    err error
}

func initialModel() model {
    ti := textinput.New()
    ti.Placeholder = "Pikachu"
    ti.Focus()
    ti.CharLimit = 156
    ti.Width = 20

    return model{
        textInput: ti,
        err: nil,
    }
}

func (m model) Init() tea.Cmd {
    return textinput.Blink
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmd tea.Cmd

    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.Type {
        case tea.KeyEnter, tea.KeyCtrlC, tea.KeyEsc:
            return m, tea.Quit
        }

    case errMsg:
        m.err = msg
        return m, nil
    }

    m.textInput, cmd = m.textInput.Update(msg)
    return m, cmd
}

func (m model) View() string {
    return fmt.Sprintf(
        "What's your favorite Pokémon?\n\n%s\n\n%s",
        m.textInput.View(),
        "(esc to quit)",
    ) + "\n"
}
```

### Advanced Example: HTTP Requests with Commands
```go
package main

import (
    "fmt"
    "net/http"
    "time"

    tea "github.com/charmbracelet/bubbletea"
)

const url = "https://httpbin.org/delay/1"

type model struct {
    status int
    err    error
}

type statusMsg int
type errMsg struct{ err error }

func checkServer() tea.Cmd {
    return func() tea.Msg {
        c := &http.Client{Timeout: 10 * time.Second}
        res, err := c.Get(url)
        if err != nil {
            return errMsg{err}
        }
        defer res.Body.Close()
        return statusMsg(res.StatusCode)
    }
}

func (m model) Init() tea.Cmd {
    return checkServer()
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case statusMsg:
        m.status = int(msg)
        return m, tea.Quit

    case errMsg:
        m.err = msg.err
        return m, tea.Quit

    case tea.KeyMsg:
        if msg.Type == tea.KeyCtrlC {
            return m, tea.Quit
        }
    }

    return m, nil
}

func (m model) View() string {
    if m.err != nil {
        return fmt.Sprintf("Error: %v\n", m.err)
    }

    if m.status > 0 {
        return fmt.Sprintf("Status: %d\n", m.status)
    }

    return "Checking server...\n"
}

func main() {
    if _, err := tea.NewProgram(model{}).Run(); err != nil {
        fmt.Printf("Error: %v", err)
    }
}
```

---

## Best Practices & Patterns

### Performance Optimization

#### Keep the Event Loop Fast
- **Rule**: Never block in `Update()` or `View()` methods
- **Practice**: Offload expensive operations to commands
- **Example**:

```go
// Bad: Blocking operation in Update
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        if msg.String() == "l" {
            // DON'T DO THIS - blocks the UI
            data := loadLargeFile() // Takes 5 seconds
            m.data = data
        }
    }
    return m, nil
}

// Good: Use commands for async operations
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        if msg.String() == "l" {
            m.loading = true
            return m, loadFileCmd() // Non-blocking
        }
    case fileLoadedMsg:
        m.data = msg.data
        m.loading = false
    }
    return m, nil
}

func loadFileCmd() tea.Cmd {
    return func() tea.Msg {
        data := loadLargeFile() // Runs in goroutine
        return fileLoadedMsg{data: data}
    }
}
```

#### Message Handling Best Practices
- **Process messages quickly**: Handle events and return immediately
- **Use type switches**: Efficient message routing
- **Batch commands**: Use `tea.Batch()` for multiple operations

```go
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmds []tea.Cmd
    
    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.String() {
        case "r":
            m.refreshing = true
            cmds = append(cmds, 
                fetchDataCmd(),
                showSpinnerCmd(),
                logActionCmd("refresh"),
            )
        }
    }
    
    return m, tea.Batch(cmds...)
}
```

### Architecture Patterns

#### Model Composition for Complex Apps
Structure large applications using model composition:

```go
type rootModel struct {
    currentView  view
    windowWidth  int
    windowHeight int
    
    // Child models
    dashboard    dashboardModel
    settings     settingsModel
    userProfile  profileModel
}

type view int
const (
    dashboardView view = iota
    settingsView
    profileView
)

func (m rootModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmd tea.Cmd
    
    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.String() {
        case "tab":
            m.currentView = (m.currentView + 1) % 3
            return m, nil
        case "q":
            return m, tea.Quit
        }
    }
    
    // Route to active view
    switch m.currentView {
    case dashboardView:
        newDashboard, cmd := m.dashboard.Update(msg)
        m.dashboard = newDashboard.(dashboardModel)
    case settingsView:
        newSettings, cmd := m.settings.Update(msg)
        m.settings = newSettings.(settingsModel)
    case profileView:
        newProfile, cmd := m.userProfile.Update(msg)
        m.userProfile = newProfile.(profileModel)
    }
    
    return m, cmd
}
```

#### State Machine Implementation
For complex workflows with multiple stages:

```go
type AppState int

const (
    StateLogin AppState = iota
    StateLoading
    StateDashboard
    StateError
)

type model struct {
    state   AppState
    err     error
    user    User
    
    // State-specific models
    loginForm    loginModel
    dashboard    dashboardModel
    spinner      spinner.Model
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch m.state {
    case StateLogin:
        return m.updateLogin(msg)
    case StateLoading:
        return m.updateLoading(msg)
    case StateDashboard:
        return m.updateDashboard(msg)
    case StateError:
        return m.updateError(msg)
    }
    return m, nil
}

func (m model) updateLogin(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case loginSuccessMsg:
        m.state = StateLoading
        m.user = msg.user
        return m, loadDashboardCmd()
    case loginErrorMsg:
        m.state = StateError
        m.err = msg.err
        return m, nil
    }
    
    var cmd tea.Cmd
    m.loginForm, cmd = m.loginForm.Update(msg)
    return m, cmd
}
```

### Error Handling Patterns

#### Graceful Error Recovery
```go
type model struct {
    data     []Item
    err      error
    retries  int
    maxRetries int
}

type errorMsg struct {
    err     error
    retryable bool
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case errorMsg:
        m.err = msg.err
        
        if msg.retryable && m.retries < m.maxRetries {
            m.retries++
            return m, tea.Batch(
                waitCmd(time.Second * time.Duration(m.retries)),
                retryCmd(),
            )
        }
        
        return m, nil
    }
    return m, nil
}
```

### Debugging and Development

#### Debugging Techniques
```go
import (
    "log"
    "os"
)

// Set up logging to file for debugging
func init() {
    logFile, err := os.OpenFile("debug.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
    if err != nil {
        panic(err)
    }
    log.SetOutput(logFile)
}

// Log messages for debugging
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    log.Printf("Received message: %+v", msg)
    
    switch msg := msg.(type) {
    case tea.KeyMsg:
        log.Printf("Key pressed: %s", msg.String())
    }
    
    return m, nil
}
```

#### Live Development Setup
```bash
# Use air for live reloading during development
go install github.com/cosmtrek/air@latest

# Create .air.toml
echo 'root = "."
cmd = "go build -o ./tmp/main ."
bin = "./tmp/main"' > .air.toml

# Run with live reload
air
```

### Testing Patterns

#### Unit Testing Models
```go
func TestModelUpdate(t *testing.T) {
    m := initialModel()
    
    // Test key handling
    newModel, cmd := m.Update(tea.KeyMsg{Type: tea.KeyEnter})
    
    if cmd == nil {
        t.Error("Expected command to be returned")
    }
    
    if newModel.(model).selectedItem == "" {
        t.Error("Expected item to be selected")
    }
}
```

#### Integration Testing with teatest
```go
import "github.com/charmbracelet/x/exp/teatest"

func TestAppFlow(t *testing.T) {
    tm := teatest.NewTestModel(
        t, initialModel(),
        teatest.WithInitialTermSize(80, 24),
    )
    
    // Send key presses
    tm.Send(tea.KeyMsg{Type: tea.KeyDown})
    tm.Send(tea.KeyMsg{Type: tea.KeyEnter})
    
    // Verify final state
    fm := tm.FinalModel(t)
    m, ok := fm.(model)
    if !ok {
        t.Fatal("Final model has unexpected type")
    }
    
    if m.selectedItem != "expected" {
        t.Errorf("Expected 'expected', got %s", m.selectedItem)
    }
}
```

### Common Anti-Patterns to Avoid

#### ❌ Don't Block the Event Loop
```go
// DON'T DO THIS
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    time.Sleep(time.Second) // Blocks UI
    return m, nil
}
```

#### ❌ Don't Ignore Error States
```go
// DON'T DO THIS
func (m model) View() string {
    return m.data.String() // Could panic if data is nil
}

// DO THIS
func (m model) View() string {
    if m.err != nil {
        return fmt.Sprintf("Error: %v", m.err)
    }
    if m.data == nil {
        return "Loading..."
    }
    return m.data.String()
}
```

#### ❌ Don't Use Goroutines Directly
```go
// DON'T DO THIS
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    go func() {
        // This bypasses Bubbletea's message system
        result := doWork()
        // No way to get result back to model
    }()
    return m, nil
}

// DO THIS
func workCmd() tea.Cmd {
    return func() tea.Msg {
        result := doWork()
        return workCompleteMsg{result: result}
    }
}
```

---

## Common Entry Points & Templates

### Project Setup and Dependencies

#### go.mod Template
```go
module mytuiapp

go 1.21

require (
    github.com/charmbracelet/bubbletea v0.24.2
    github.com/charmbracelet/bubbles v0.16.1
    github.com/charmbracelet/lipgloss v0.8.0
)
```

#### Installation Commands
```bash
# Initialize Go module
go mod init mytuiapp

# Install core dependencies
go get github.com/charmbracelet/bubbletea@latest
go get github.com/charmbracelet/bubbles@latest
go get github.com/charmbracelet/lipgloss@latest

# Optional: Testing utilities
go get github.com/charmbracelet/x/exp/teatest@latest
```

### Standard main.go Templates

#### Basic Application Template
```go
package main

import (
    "fmt"
    "os"

    tea "github.com/charmbracelet/bubbletea"
)

type model struct {
    // Define your application state here
    cursor   int
    choices  []string
    selected map[int]struct{}
}

func initialModel() model {
    return model{
        choices:  []string{"Option 1", "Option 2", "Option 3"},
        selected: make(map[int]struct{}),
    }
}

func (m model) Init() tea.Cmd {
    // Return initial command (if any)
    return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.String() {
        case "ctrl+c", "q":
            return m, tea.Quit
        case "up", "k":
            if m.cursor > 0 {
                m.cursor--
            }
        case "down", "j":
            if m.cursor < len(m.choices)-1 {
                m.cursor++
            }
        case " ":
            _, ok := m.selected[m.cursor]
            if ok {
                delete(m.selected, m.cursor)
            } else {
                m.selected[m.cursor] = struct{}{}
            }
        }
    }
    return m, nil
}

func (m model) View() string {
    s := "What should we buy at the market?\n\n"

    for i, choice := range m.choices {
        cursor := " "
        if m.cursor == i {
            cursor = ">"
        }

        checked := " "
        if _, ok := m.selected[i]; ok {
            checked = "x"
        }

        s += fmt.Sprintf("%s [%s] %s\n", cursor, checked, choice)
    }

    s += "\nPress q to quit.\n"
    return s
}

func main() {
    p := tea.NewProgram(initialModel())
    if _, err := p.Run(); err != nil {
        fmt.Printf("Alas, there's been an error: %v", err)
        os.Exit(1)
    }
}
```

#### Application with Configuration
```go
package main

import (
    "flag"
    "fmt"
    "os"

    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/lipgloss"
)

type Config struct {
    Debug    bool
    LogFile  string
    Theme    string
    Width    int
    Height   int
}

func parseFlags() Config {
    var config Config
    flag.BoolVar(&config.Debug, "debug", false, "Enable debug mode")
    flag.StringVar(&config.LogFile, "log", "", "Log file path")
    flag.StringVar(&config.Theme, "theme", "default", "Color theme")
    flag.IntVar(&config.Width, "width", 80, "Terminal width")
    flag.IntVar(&config.Height, "height", 24, "Terminal height")
    flag.Parse()
    return config
}

type model struct {
    config Config
    ready  bool
    // ... other fields
}

func initialModel(config Config) model {
    return model{
        config: config,
        ready:  false,
    }
}

func (m model) Init() tea.Cmd {
    return tea.Batch(
        tea.EnterAltScreen,
        initCmd(m.config),
    )
}

func main() {
    config := parseFlags()
    
    var opts []tea.ProgramOption
    if config.Debug {
        // Setup debug logging
        if config.LogFile != "" {
            f, err := tea.LogToFile(config.LogFile, "debug")
            if err != nil {
                fmt.Println("fatal:", err)
                os.Exit(1)
            }
            defer f.Close()
        }
    }
    
    p := tea.NewProgram(initialModel(config), opts...)
    if _, err := p.Run(); err != nil {
        fmt.Printf("Error: %v", err)
        os.Exit(1)
    }
}
```

#### Multi-View Application Template
```go
package main

import (
    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/bubbles/list"
    "github.com/charmbracelet/bubbles/textinput"
)

type sessionState int

const (
    listView sessionState = iota
    inputView
    resultsView
)

type mainModel struct {
    state   sessionState
    list    list.Model
    input   textinput.Model
    results []string
    width   int
    height  int
}

func newMainModel() mainModel {
    // Initialize list
    items := []list.Item{/* ... */}
    listModel := list.New(items, list.NewDefaultDelegate(), 0, 0)
    
    // Initialize input
    inputModel := textinput.New()
    inputModel.Placeholder = "Enter your query..."
    
    return mainModel{
        state:  listView,
        list:   listModel,
        input:  inputModel,
    }
}

func (m mainModel) Init() tea.Cmd {
    return nil
}

func (m mainModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width = msg.Width
        m.height = msg.Height
        m.list.SetSize(msg.Width, msg.Height-3)
        m.input.Width = msg.Width - 4
    
    case tea.KeyMsg:
        switch msg.String() {
        case "ctrl+c":
            return m, tea.Quit
        case "tab":
            return m.switchView()
        }
    }
    
    // Delegate to current view
    return m.updateCurrentView(msg)
}

func (m mainModel) switchView() (mainModel, tea.Cmd) {
    switch m.state {
    case listView:
        m.state = inputView
        m.input.Focus()
        return m, textinput.Blink
    case inputView:
        m.state = resultsView
        m.input.Blur()
        return m, nil
    case resultsView:
        m.state = listView
        return m, nil
    }
    return m, nil
}

func (m mainModel) updateCurrentView(msg tea.Msg) (mainModel, tea.Cmd) {
    var cmd tea.Cmd
    
    switch m.state {
    case listView:
        m.list, cmd = m.list.Update(msg)
    case inputView:
        m.input, cmd = m.input.Update(msg)
    case resultsView:
        // Handle results view updates
    }
    
    return m, cmd
}

func (m mainModel) View() string {
    switch m.state {
    case listView:
        return m.list.View()
    case inputView:
        return fmt.Sprintf("Input:\n%s", m.input.View())
    case resultsView:
        return "Results view"
    }
    return ""
}
```

### Project Structure Recommendations

```
mytuiapp/
├── main.go              # Application entry point
├── go.mod               # Go module definition
├── README.md            # Project documentation
└── internal/            # Internal packages
    ├── models/          # Bubbletea models
    │   ├── app.go
    │   ├── list.go
    │   └── input.go
    ├── commands/        # Async commands
    │   ├── http.go
    │   └── files.go
    ├── styles/          # Lipgloss styles
    │   └── theme.go
    └── messages/        # Message types
        └── types.go
```

### Environment and Configuration

#### Environment Variables
```go
package main

import (
    "os"
    "strconv"
)

type Config struct {
    Debug      bool
    LogLevel   string
    APIKey     string
    MaxRetries int
}

func loadConfig() Config {
    config := Config{
        Debug:      getEnvBool("DEBUG", false),
        LogLevel:   getEnv("LOG_LEVEL", "info"),
        APIKey:     getEnv("API_KEY", ""),
        MaxRetries: getEnvInt("MAX_RETRIES", 3),
    }
    return config
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
    if value := os.Getenv(key); value != "" {
        if parsed, err := strconv.ParseBool(value); err == nil {
            return parsed
        }
    }
    return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
    if value := os.Getenv(key); value != "" {
        if parsed, err := strconv.Atoi(value); err == nil {
            return parsed
        }
    }
    return defaultValue
}
```

---

## LLM-Optimized Reference

### Quick Reference FAQ

#### Q: How do I create a new Bubbletea application?
A: Create a struct implementing `Init() tea.Cmd`, `Update(tea.Msg) (tea.Model, tea.Cmd)`, and `View() string`, then call `tea.NewProgram(model{}).Run()`.

#### Q: How do I handle user input?
A: Handle `tea.KeyMsg` in your `Update()` method: `case tea.KeyMsg: switch msg.String() { case "q": return m, tea.Quit }`

#### Q: How do I perform async operations?
A: Use commands that return messages: `func asyncCmd() tea.Cmd { return func() tea.Msg { /* work */ return resultMsg{} } }`

#### Q: How do I style text and layout?
A: Use Lip Gloss: `style := lipgloss.NewStyle().Foreground(lipgloss.Color("#ff0000"))` then `style.Render("text")`

#### Q: How do I create lists?
A: Use the bubbles list component: `list.New(items, list.NewDefaultDelegate(), width, height)`

#### Q: How do I handle window resize?
A: Handle `tea.WindowSizeMsg`: `case tea.WindowSizeMsg: m.width = msg.Width; m.height = msg.Height`

#### Q: How do I quit the application?
A: Return `tea.Quit` command: `return m, tea.Quit`

#### Q: How do I show loading states?
A: Use spinner component: `spinner.New()` and handle `spinner.TickMsg` in Update

#### Q: How do I handle errors?
A: Define error message types and handle them in Update: `type errMsg struct{ err error }`

#### Q: How do I create forms?
A: Use textinput components for each field and manage focus states manually

### Common Code Snippets

#### Basic Application Structure
```go
type model struct {
    // State here
}

func (m model) Init() tea.Cmd { return nil }
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        if msg.String() == "q" { return m, tea.Quit }
    }
    return m, nil
}
func (m model) View() string { return "Hello" }
```

#### Async HTTP Request
```go
func httpCmd(url string) tea.Cmd {
    return func() tea.Msg {
        resp, err := http.Get(url)
        if err != nil { return errMsg{err} }
        defer resp.Body.Close()
        return httpResponseMsg{resp.StatusCode}
    }
}
```

#### List with Selection
```go
items := []list.Item{item("Option 1"), item("Option 2")}
l := list.New(items, list.NewDefaultDelegate(), 20, 10)
l.Title = "Choose one"
```

#### Text Input with Validation
```go
ti := textinput.New()
ti.Placeholder = "Enter text"
ti.Focus()
ti.CharLimit = 50
```

#### Styled Layout
```go
header := lipgloss.NewStyle().Bold(true).Render("Title")
content := lipgloss.NewStyle().Padding(1).Render("Content")
return lipgloss.JoinVertical(lipgloss.Left, header, content)
```

### Message Type Patterns

#### Standard Message Types
```go
// User actions
type itemSelectedMsg struct{ item string }
type formSubmittedMsg struct{ data FormData }

// System events  
type dataLoadedMsg struct{ data []Item }
type errorMsg struct{ err error }
type timeoutMsg struct{}

// Network responses
type httpResponseMsg struct{ status int; body []byte }
type apiErrorMsg struct{ code int; message string }
```

#### Command Patterns
```go
// Data loading
func loadDataCmd() tea.Cmd {
    return func() tea.Msg {
        data, err := fetchData()
        if err != nil { return errorMsg{err} }
        return dataLoadedMsg{data}
    }
}

// Timer/Delay
func delayCmd(d time.Duration) tea.Cmd {
    return tea.Tick(d, func(time.Time) tea.Msg {
        return timeoutMsg{}
    })
}

// File operations
func readFileCmd(path string) tea.Cmd {
    return func() tea.Msg {
        content, err := os.ReadFile(path)
        if err != nil { return errorMsg{err} }
        return fileLoadedMsg{path, content}
    }
}
```

### Key Binding Patterns

#### Standard Navigation
```go
case tea.KeyMsg:
    switch msg.String() {
    case "q", "ctrl+c": return m, tea.Quit
    case "up", "k": m.cursor--
    case "down", "j": m.cursor++
    case "enter", " ": return m, selectCmd()
    case "esc": return m, cancelCmd()
    case "tab": return m.switchView()
    }
```

#### Form Navigation
```go
switch msg.String() {
case "tab":
    m.focusIndex = (m.focusIndex + 1) % len(m.inputs)
    return m, m.updateFocus()
case "shift+tab":
    m.focusIndex--
    if m.focusIndex < 0 { m.focusIndex = len(m.inputs) - 1 }
    return m, m.updateFocus()
case "enter":
    if m.focusIndex == len(m.inputs) { return m, submitCmd() }
}
```

### Error Handling Patterns

#### Graceful Degradation
```go
func (m model) View() string {
    if m.err != nil {
        return errorView(m.err)
    }
    if m.loading {
        return loadingView()
    }
    if len(m.data) == 0 {
        return emptyStateView()
    }
    return normalView(m.data)
}
```

#### Retry Logic
```go
case errorMsg:
    m.err = msg.err
    if m.retries < maxRetries {
        m.retries++
        return m, tea.Sequence(
            delayCmd(time.Second * time.Duration(m.retries)),
            retryCmd(),
        )
    }
    return m, nil
```

### Performance Tips

#### Efficient Updates
- Only update what changed in your model
- Use `tea.Batch()` for multiple commands
- Avoid expensive operations in `View()`
- Cache rendered content when possible

#### Memory Management
- Limit list sizes for large datasets
- Use pagination for big collections
- Clean up resources in commands
- Avoid memory leaks in long-running apps

### Troubleshooting Guide

#### Q: My app is laggy/unresponsive
A: Check if you're blocking in `Update()` or `View()`. Move expensive operations to commands.

#### Q: Commands aren't working
A: Ensure commands return messages that are handled in `Update()`. Check for nil command returns.

#### Q: Styling isn't applied
A: Verify Lip Gloss styles are called with `.Render()`. Check terminal color support.

#### Q: Components don't respond to input
A: Make sure to call component's `Update()` method and handle their specific message types.

#### Q: App crashes on resize
A: Handle `tea.WindowSizeMsg` and update component dimensions appropriately.

#### Q: Text input cursor not visible
A: Call `Focus()` on text input and ensure `textinput.Blink` command is returned in `Init()`.

### Integration Examples

#### With CLI Libraries (cobra)
```go
var rootCmd = &cobra.Command{
    Use: "myapp",
    Run: func(cmd *cobra.Command, args []string) {
        p := tea.NewProgram(initialModel())
        if _, err := p.Run(); err != nil {
            log.Fatal(err)
        }
    },
}
```

#### With Configuration (viper)
```go
func loadConfig() Config {
    viper.SetDefault("theme", "default")
    viper.ReadInConfig()
    return Config{
        Theme: viper.GetString("theme"),
        Debug: viper.GetBool("debug"),
    }
}
```

#### With Logging (logrus)
```go
func init() {
    log.SetOutput(os.Stderr)
    tea.LogToFile("debug.log", "debug")
}
```
