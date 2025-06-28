# Dotfiles TUI Manager Makefile
# Go project build automation with best practices

# Project configuration
BINARY_NAME := dotfiles
MAIN_PACKAGE := ./cmd/dotfiles
GO_VERSION := 1.21
PROJECT_NAME := dotfiles-tui-manager

# Build configuration
BUILD_DIR := bin
DIST_DIR := dist
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_TIME := $(shell date -u '+%Y-%m-%d_%H:%M:%S')

# Go build flags
LDFLAGS := -ldflags "-s -w -X main.version=$(VERSION) -X main.commit=$(COMMIT) -X main.buildTime=$(BUILD_TIME)"
GCFLAGS := -gcflags="all=-trimpath=$(PWD)"
ASMFLAGS := -asmflags="all=-trimpath=$(PWD)"

# Platform targets
PLATFORMS := darwin/amd64 darwin/arm64 linux/amd64 linux/arm64 windows/amd64

# Test configuration
TEST_TIMEOUT := 30s
TEST_COVERAGE_THRESHOLD := 80
INTEGRATION_TEST_TIMEOUT := 5m

# Colors for output
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m
COLOR_MAGENTA := \033[35m

.PHONY: help
help: ## Show this help message
	@echo "$(COLOR_BOLD)$(PROJECT_NAME) - Makefile Help$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)Usage:$(COLOR_RESET)"
	@echo "  make <target>"
	@echo ""
	@echo "$(COLOR_BOLD)Available targets:$(COLOR_RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(COLOR_BLUE)%-20s$(COLOR_RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# =============================================================================
# Build targets
# =============================================================================

.PHONY: build
build: clean ## Build the binary for current platform
	@echo "$(COLOR_GREEN)Building $(BINARY_NAME) for current platform...$(COLOR_RESET)"
	@mkdir -p $(BUILD_DIR)
	@go build $(LDFLAGS) $(GCFLAGS) $(ASMFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME) $(MAIN_PACKAGE)
	@echo "$(COLOR_GREEN)✓ Binary built: $(BUILD_DIR)/$(BINARY_NAME)$(COLOR_RESET)"

.PHONY: build-debug
build-debug: clean ## Build the binary with debug symbols
	@echo "$(COLOR_GREEN)Building $(BINARY_NAME) with debug symbols...$(COLOR_RESET)"
	@mkdir -p $(BUILD_DIR)
	@go build -race -o $(BUILD_DIR)/$(BINARY_NAME)-debug $(MAIN_PACKAGE)
	@echo "$(COLOR_GREEN)✓ Debug binary built: $(BUILD_DIR)/$(BINARY_NAME)-debug$(COLOR_RESET)"

.PHONY: build-all
build-all: clean ## Build binaries for all supported platforms
	@echo "$(COLOR_GREEN)Building $(BINARY_NAME) for all platforms...$(COLOR_RESET)"
	@mkdir -p $(DIST_DIR)
	@for platform in $(PLATFORMS); do \
		os=$${platform%/*}; \
		arch=$${platform#*/}; \
		output_name=$(BINARY_NAME)-$$os-$$arch; \
		if [ "$$os" = "windows" ]; then output_name=$${output_name}.exe; fi; \
		echo "$(COLOR_BLUE)Building for $$os/$$arch...$(COLOR_RESET)"; \
		env GOOS=$$os GOARCH=$$arch go build $(LDFLAGS) $(GCFLAGS) $(ASMFLAGS) -o $(DIST_DIR)/$$output_name $(MAIN_PACKAGE); \
		if [ $$? -ne 0 ]; then echo "$(COLOR_RED)✗ Failed to build for $$os/$$arch$(COLOR_RESET)"; exit 1; fi; \
	done
	@echo "$(COLOR_GREEN)✓ All platform binaries built in $(DIST_DIR)/$(COLOR_RESET)"

.PHONY: install
install: build ## Install the binary to $GOPATH/bin or /usr/local/bin
	@echo "$(COLOR_GREEN)Installing $(BINARY_NAME)...$(COLOR_RESET)"
	@if [ -n "$(GOPATH)" ] && [ -d "$(GOPATH)/bin" ]; then \
		cp $(BUILD_DIR)/$(BINARY_NAME) $(GOPATH)/bin/; \
		echo "$(COLOR_GREEN)✓ Installed to $(GOPATH)/bin/$(BINARY_NAME)$(COLOR_RESET)"; \
	elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then \
		cp $(BUILD_DIR)/$(BINARY_NAME) /usr/local/bin/; \
		echo "$(COLOR_GREEN)✓ Installed to /usr/local/bin/$(BINARY_NAME)$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_YELLOW)Warning: Could not find writable installation directory$(COLOR_RESET)"; \
		echo "$(COLOR_YELLOW)Please manually copy $(BUILD_DIR)/$(BINARY_NAME) to your PATH$(COLOR_RESET)"; \
	fi

.PHONY: uninstall
uninstall: ## Remove the installed binary
	@echo "$(COLOR_GREEN)Uninstalling $(BINARY_NAME)...$(COLOR_RESET)"
	@if [ -n "$(GOPATH)" ] && [ -f "$(GOPATH)/bin/$(BINARY_NAME)" ]; then \
		rm -f $(GOPATH)/bin/$(BINARY_NAME); \
		echo "$(COLOR_GREEN)✓ Removed from $(GOPATH)/bin/$(COLOR_RESET)"; \
	fi
	@if [ -f "/usr/local/bin/$(BINARY_NAME)" ]; then \
		rm -f /usr/local/bin/$(BINARY_NAME); \
		echo "$(COLOR_GREEN)✓ Removed from /usr/local/bin/$(COLOR_RESET)"; \
	fi

# =============================================================================
# Test targets
# =============================================================================

.PHONY: test
test: ## Run unit tests
	@echo "$(COLOR_GREEN)Running unit tests...$(COLOR_RESET)"
	@go test -timeout $(TEST_TIMEOUT) -race -v ./...

.PHONY: test-short
test-short: ## Run unit tests in short mode
	@echo "$(COLOR_GREEN)Running unit tests (short mode)...$(COLOR_RESET)"
	@go test -short -timeout $(TEST_TIMEOUT) -race -v ./...

.PHONY: test-integration
test-integration: ## Run integration tests
	@echo "$(COLOR_GREEN)Running integration tests...$(COLOR_RESET)"
	@go test -timeout $(INTEGRATION_TEST_TIMEOUT) -tags=integration -v ./test/integration/...

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(COLOR_GREEN)Running tests with coverage...$(COLOR_RESET)"
	@mkdir -p $(BUILD_DIR)
	@go test -timeout $(TEST_TIMEOUT) -race -coverprofile=$(BUILD_DIR)/coverage.out -covermode=atomic ./...
	@go tool cover -html=$(BUILD_DIR)/coverage.out -o $(BUILD_DIR)/coverage.html
	@go tool cover -func=$(BUILD_DIR)/coverage.out | tail -1 | awk '{print "$(COLOR_GREEN)Total coverage: " $$3 "$(COLOR_RESET)"}'
	@echo "$(COLOR_BLUE)Coverage report: $(BUILD_DIR)/coverage.html$(COLOR_RESET)"

.PHONY: test-coverage-check
test-coverage-check: test-coverage ## Check if coverage meets threshold
	@coverage=$$(go tool cover -func=$(BUILD_DIR)/coverage.out | tail -1 | awk '{print $$3}' | sed 's/%//'); \
	if [ $$(echo "$$coverage >= $(TEST_COVERAGE_THRESHOLD)" | bc -l) -eq 1 ]; then \
		echo "$(COLOR_GREEN)✓ Coverage $$coverage% meets threshold $(TEST_COVERAGE_THRESHOLD)%$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_RED)✗ Coverage $$coverage% below threshold $(TEST_COVERAGE_THRESHOLD)%$(COLOR_RESET)"; \
		exit 1; \
	fi

.PHONY: bench
bench: ## Run benchmarks (excluding long-running performance tests)
	@echo "$(COLOR_GREEN)Running benchmarks...$(COLOR_RESET)"
	@go test -bench=. -benchmem -run=^$$ ./... | grep -v "BenchmarkConcurrentCache\|BenchmarkMemoryAllocations\|StressTest"

# =============================================================================
# Code quality targets
# =============================================================================

.PHONY: fmt
fmt: ## Format Go code
	@echo "$(COLOR_GREEN)Formatting Go code...$(COLOR_RESET)"
	@go fmt ./...

.PHONY: fmt-check
fmt-check: ## Check if code is formatted
	@echo "$(COLOR_GREEN)Checking code formatting...$(COLOR_RESET)"
	@unformatted=$$(go fmt ./...); \
	if [ -n "$$unformatted" ]; then \
		echo "$(COLOR_RED)✗ Code is not formatted. Run 'make fmt' to fix:$(COLOR_RESET)"; \
		echo "$$unformatted"; \
		exit 1; \
	else \
		echo "$(COLOR_GREEN)✓ Code is properly formatted$(COLOR_RESET)"; \
	fi

.PHONY: vet
vet: ## Run go vet
	@echo "$(COLOR_GREEN)Running go vet...$(COLOR_RESET)"
	@go vet ./...

.PHONY: lint
lint: ## Run golangci-lint
	@echo "$(COLOR_GREEN)Running golangci-lint...$(COLOR_RESET)"
	@if command -v golangci-lint >/dev/null 2>&1; then \
		golangci-lint run; \
	else \
		echo "$(COLOR_YELLOW)golangci-lint not found. Install it with: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest$(COLOR_RESET)"; \
	fi

.PHONY: staticcheck
staticcheck: ## Run staticcheck
	@echo "$(COLOR_GREEN)Running staticcheck...$(COLOR_RESET)"
	@if command -v staticcheck >/dev/null 2>&1; then \
		staticcheck ./...; \
	else \
		echo "$(COLOR_YELLOW)staticcheck not found. Install it with: go install honnef.co/go/tools/cmd/staticcheck@latest$(COLOR_RESET)"; \
	fi

.PHONY: check
check: fmt-check vet lint staticcheck ## Run all code quality checks

# =============================================================================
# Development targets
# =============================================================================

.PHONY: run
run: ## Run the application in TUI mode
	@echo "$(COLOR_GREEN)Starting $(BINARY_NAME) TUI...$(COLOR_RESET)"
	@go run $(MAIN_PACKAGE) tui

.PHONY: run-cli
run-cli: ## Run the application in CLI mode with status
	@echo "$(COLOR_GREEN)Running $(BINARY_NAME) CLI status...$(COLOR_RESET)"
	@go run $(MAIN_PACKAGE) status

.PHONY: deps
deps: ## Download and verify dependencies
	@echo "$(COLOR_GREEN)Downloading dependencies...$(COLOR_RESET)"
	@go mod download
	@go mod verify

.PHONY: mod-tidy
mod-tidy: ## Tidy go modules
	@echo "$(COLOR_GREEN)Tidying go modules...$(COLOR_RESET)"
	@go mod tidy

.PHONY: mod-update
mod-update: ## Update all dependencies to their latest minor versions
	@echo "$(COLOR_GREEN)Updating dependencies...$(COLOR_RESET)"
	@go get -u ./...
	@go mod tidy

.PHONY: generate
generate: ## Run go generate
	@echo "$(COLOR_GREEN)Running go generate...$(COLOR_RESET)"
	@go generate ./...

# =============================================================================
# Release targets
# =============================================================================

.PHONY: tag
tag: ## Create a new git tag (usage: make tag VERSION=v1.0.0)
	@if [ -z "$(VERSION)" ]; then echo "Usage: make tag VERSION=v1.0.0"; exit 1; fi
	@echo "$(COLOR_GREEN)Creating tag $(VERSION)...$(COLOR_RESET)"
	@git tag -a $(VERSION) -m "Release $(VERSION)"
	@echo "$(COLOR_GREEN)✓ Tag $(VERSION) created. Push with: git push origin $(VERSION)$(COLOR_RESET)"

.PHONY: release
release: clean test check build-all ## Build release binaries
	@echo "$(COLOR_GREEN)Creating release archives...$(COLOR_RESET)"
	@mkdir -p $(DIST_DIR)/archives
	@for platform in $(PLATFORMS); do \
		os=$${platform%/*}; \
		arch=$${platform#*/}; \
		binary_name=$(BINARY_NAME)-$$os-$$arch; \
		if [ "$$os" = "windows" ]; then binary_name=$${binary_name}.exe; fi; \
		archive_name=$(BINARY_NAME)-$(VERSION)-$$os-$$arch; \
		if [ "$$os" = "windows" ]; then \
			zip -j $(DIST_DIR)/archives/$${archive_name}.zip $(DIST_DIR)/$$binary_name README.md LICENSE 2>/dev/null || true; \
		else \
			tar -czf $(DIST_DIR)/archives/$${archive_name}.tar.gz -C $(DIST_DIR) $$binary_name -C .. README.md LICENSE 2>/dev/null || \
			tar -czf $(DIST_DIR)/archives/$${archive_name}.tar.gz -C $(DIST_DIR) $$binary_name; \
		fi; \
	done
	@echo "$(COLOR_GREEN)✓ Release archives created in $(DIST_DIR)/archives/$(COLOR_RESET)"

# =============================================================================
# Cleanup targets
# =============================================================================

.PHONY: clean
clean: ## Clean build artifacts
	@echo "$(COLOR_GREEN)Cleaning build artifacts...$(COLOR_RESET)"
	@rm -rf $(BUILD_DIR) $(DIST_DIR)

.PHONY: clean-deps
clean-deps: clean ## Clean dependencies cache
	@echo "$(COLOR_GREEN)Cleaning dependencies cache...$(COLOR_RESET)"
	@go clean -modcache

# =============================================================================
# Docker targets (optional)
# =============================================================================

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(COLOR_GREEN)Building Docker image...$(COLOR_RESET)"
	@docker build -t $(PROJECT_NAME):$(VERSION) -t $(PROJECT_NAME):latest .

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "$(COLOR_GREEN)Running Docker container...$(COLOR_RESET)"
	@docker run --rm -it $(PROJECT_NAME):latest

# =============================================================================
# Information targets
# =============================================================================

.PHONY: info
info: ## Show project information
	@echo "$(COLOR_BOLD)Project Information$(COLOR_RESET)"
	@echo "Name:          $(PROJECT_NAME)"
	@echo "Binary:        $(BINARY_NAME)"
	@echo "Version:       $(VERSION)"
	@echo "Commit:        $(COMMIT)"
	@echo "Build Time:    $(BUILD_TIME)"
	@echo "Go Version:    $(shell go version)"
	@echo "Build Dir:     $(BUILD_DIR)"
	@echo "Dist Dir:      $(DIST_DIR)"

.PHONY: env
env: ## Show environment information
	@echo "$(COLOR_BOLD)Environment Information$(COLOR_RESET)"
	@echo "GOPATH:        $(GOPATH)"
	@echo "GOROOT:        $(GOROOT)"
	@echo "GOOS:          $(shell go env GOOS)"
	@echo "GOARCH:        $(shell go env GOARCH)"
	@echo "CGO_ENABLED:   $(shell go env CGO_ENABLED)"

# Default target
.DEFAULT_GOAL := help