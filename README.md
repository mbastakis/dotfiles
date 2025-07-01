# Dotfiles TUI Manager

A modern, interactive Terminal User Interface (TUI) for managing your dotfiles with advanced features including theming, performance optimization, and comprehensive tool integration.

## ✨ Features

- **🖥️ Interactive TUI**: Modern terminal interface with intuitive navigation
- **📦 Package Management**: GNU Stow integration with dependency handling
- **🛠️ Tool Integration**: Support for Homebrew, NPM, APT, Pip, and more
- **🎨 Advanced Theming**: Customizable color schemes with live preview
- **⚡ Performance Optimized**: Object pooling, caching, and memory monitoring
- **🧪 Comprehensive Testing**: Full test coverage with unit and integration tests
- **📚 Rich Documentation**: Complete guides and API documentation
- **🔄 Migration Tools**: Easy migration from existing dotfiles setups

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/mbastakis/dotfiles ~/.dotfiles
cd ~/.dotfiles

# Build the application
go build -o dotfiles cmd/main.go

# Make it available globally
sudo mv dotfiles /usr/local/bin/

# Initialize configuration
dotfiles init
```

### First Launch

```bash
# Start the interactive TUI
dotfiles tui
```

Follow the setup wizard to configure your dotfiles directory, package preferences, and theme selection.

## 📖 Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete guide to using the TUI manager
- **[Configuration Reference](docs/CONFIGURATION.md)** - Detailed configuration options
- **[Migration Guide](docs/MIGRATION.md)** - Migrate from existing dotfiles setups
- **[Performance Guide](docs/PERFORMANCE.md)** - Optimization features and best practices

## 🖼️ Screenshots

### Main Overview
The main dashboard provides a comprehensive view of your dotfiles status:

```
┌─ Dotfiles Manager ─────────────────────────────────────────────────────────┐
│                                                                            │
│  📊 System Overview                     🎯 Quick Actions                   │
│  ├─ Packages: 12 enabled, 3 disabled   ├─ [S] Sync All Packages          │
│  ├─ Tools: 5 healthy, 0 errors         ├─ [U] Update Tools               │
│  ├─ Theme: cyberpunk                    ├─ [T] Change Theme               │
│  └─ Last Sync: 2 hours ago              └─ [C] Configuration              │
│                                                                            │
│  📈 Performance Metrics                 📋 Recent Activity                │
│  ├─ Memory: 45.2 MB                     ├─ vim package synced             │
│  ├─ Cache Hit: 94%                      ├─ homebrew updated               │
│  └─ Operations: 156 total               └─ theme changed to cyberpunk     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Package Management
Intuitive package management with real-time status:

```
┌─ Package Management ───────────────────────────────────────────────────────┐
│                                                                            │
│  Package Name     Status    Priority   Dependencies    Last Modified       │
│  ├─ [✓] git       enabled   1          -               2 days ago         │
│  ├─ [✓] vim       enabled   2          git             1 hour ago         │
│  ├─ [✓] zsh       enabled   3          git             3 hours ago        │
│  ├─ [ ] tmux      disabled  4          -               1 week ago         │
│  └─ [✓] homebrew  enabled   5          -               2 days ago         │
│                                                                            │
│  [Space] Toggle   [Enter] Configure   [D] Details   [R] Remove             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Theme Selection
Live theme preview with real-time updates:

```
┌─ Theme Selection ──────────────────────────────────────────────────────────┐
│                                                                            │
│  Available Themes               Preview                                    │
│  ├─ [ ] default                 ┌─ Preview Window ─────────────────────┐  │
│  ├─ [ ] light                   │ Primary Color: ████                  │  │
│  ├─ [●] cyberpunk               │ Secondary: ████                      │  │
│  ├─ [ ] dark                    │ Success: ████ Warning: ████         │  │
│  └─ [ ] minimal                 │ Error: ████   Background: ████      │  │
│                                 └──────────────────────────────────────┘  │
│                                                                            │
│  [Enter] Apply Theme   [C] Customize   [I] Import   [E] Export             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## 🏗️ Architecture

The project is organized into several key modules:

### Core Components

- **`internal/tui/`** - Terminal user interface implementation
- **`internal/config/`** - Configuration management system
- **`internal/theme/`** - Theme and styling system
- **`internal/tools/`** - Tool integration framework
- **`internal/perf/`** - Performance optimization utilities

### Key Features

#### Package Management (`internal/stow/`)
- GNU Stow integration for symlink management
- Dependency resolution and conflict detection
- Priority-based installation ordering
- File filtering with include/exclude patterns

#### Tool Integration (`internal/tools/`)
- Modular tool plugin system
- Support for popular package managers
- Health monitoring and status checking
- Bulk operations and synchronization

#### Performance System (`internal/perf/`)
- Object pooling for memory efficiency
- Multi-level caching with TTL
- Real-time performance monitoring
- Automatic profiling and optimization

#### Theme System (`internal/theme/`)
- Live theme switching and preview
- Custom color scheme creation
- Component-specific styling
- Import/export functionality

## 🧪 Testing

The project includes comprehensive testing with multiple levels:

### Running Tests

```bash
# Run all tests
go test ./...

# Run with coverage
go test -cover ./...

# Run integration tests
go test -tags=integration ./test/integration/

# Run benchmarks
go test -bench=. ./internal/perf/

# Run stress tests
go test -run=TestStress ./internal/perf/
```

### Test Structure

- **Unit Tests**: `*_test.go` files alongside source code
- **Integration Tests**: `test/integration/` directory
- **Benchmarks**: Performance benchmarks in `internal/perf/`
- **Test Utilities**: Shared testing utilities in `test/testutil/`

## ⚡ Performance

The system is optimized for efficiency and responsiveness:

### Optimization Features

- **Object Pooling**: Reduces allocations for frequently used objects
- **Intelligent Caching**: Multi-level caching with automatic cleanup
- **String Optimization**: Efficient string operations with minimal allocations
- **Memory Monitoring**: Real-time tracking of memory usage and GC behavior
- **Concurrent Operations**: Parallel execution where safe and beneficial

### Benchmarks

```bash
# Example benchmark results
BenchmarkStringBuilder-8         1000000    1205 ns/op     256 B/op    1 allocs/op
BenchmarkCache-8                 2000000     823 ns/op       0 B/op    0 allocs/op
BenchmarkObjectPool-8            5000000     312 ns/op       0 B/op    0 allocs/op
```

## 🔧 Configuration

### Basic Configuration

```yaml
global:
  dotfiles_path: "/Users/username/.dotfiles"
  log_level: "info"

tui:
  color_scheme: "cyberpunk"
  animations: true
  vim_mode: false

stow:
  packages:
    - name: "vim"
      enabled: true
      priority: 1
    - name: "git"
      enabled: true
      priority: 2

tools:
  homebrew:
    enabled: true
    auto_update: false
  npm:
    enabled: true
    global_packages: true
```

### Environment Variables

```bash
export DOTFILES_LOG_LEVEL=debug
export DOTFILES_THEME=cyberpunk
export DOTFILES_DRY_RUN=true
```

## 🛠️ Development

### Prerequisites

- Go 1.19 or later
- Terminal with Unicode support
- Git for version control

### Building from Source

```bash
# Clone the repository
git clone https://github.com/mbastakis/dotfiles
cd dotfiles

# Install dependencies
go mod download

# Build the application
go build -o dotfiles cmd/main.go

# Run tests
go test ./...

# Build with optimizations
go build -ldflags "-s -w" -o dotfiles cmd/main.go
```

### Development Setup

```bash
# Enable development mode
export DOTFILES_DEV_MODE=true
export DOTFILES_LOG_LEVEL=debug

# Enable profiling (optional)
export DOTFILES_PROFILE_ENABLED=true

# Run with hot reload (if using air)
air
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Process

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

### Code Standards

- Follow Go best practices and idioms
- Include unit tests for new functionality
- Update documentation for user-facing changes
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Bubble Tea](https://github.com/charmbracelet/bubbletea) for the excellent TUI framework
- [GNU Stow](https://www.gnu.org/software/stow/) for dotfiles management inspiration
- [Cobra](https://github.com/spf13/cobra) for CLI interface
- The Go community for excellent tooling and libraries

## 📞 Support

- **Documentation**: [User Guide](docs/USER_GUIDE.md) and [FAQ](docs/FAQ.md)
- **Issues**: [GitHub Issues](https://github.com/mbastakis/dotfiles/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mbastakis/dotfiles/discussions)
- **Wiki**: [Community Wiki](https://github.com/mbastakis/dotfiles/wiki)

---

Made with ❤️ for developers who love well-organized dotfiles and beautiful terminal interfaces.
