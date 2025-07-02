package homebrew

import (
	"testing"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/test/testutil"
)

func TestNewHomebrewTool(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
			DryRun:       false,
		},
		Homebrew: config.HomebrewConfig{
			AutoUpdate: true,
			Categories: map[string]config.HomebrewCategory{
				"core": {Enabled: true, Brewfile: "homebrew/Brewfile"},
			},
		},
	}

	tool := NewHomebrewTool(cfg)

	if tool == nil {
		t.Fatal("Expected NewHomebrewTool to return non-nil tool")
	}

	if tool.Name() != "homebrew" {
		t.Errorf("Expected tool name to be 'homebrew', got %s", tool.Name())
	}

	if tool.Priority() != 30 {
		t.Errorf("Expected priority to be 30, got %d", tool.Priority())
	}

	if !tool.IsEnabled() {
		t.Error("Expected tool to be enabled")
	}
}

func TestHomebrewTool_Configure(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		Homebrew: config.HomebrewConfig{
			AutoUpdate: true,
			Categories: map[string]config.HomebrewCategory{
				"core": {Enabled: true, Brewfile: "homebrew/Brewfile"},
			},
		},
	}

	tool := NewHomebrewTool(cfg)

	// Test with valid config
	newConfig := &config.HomebrewConfig{
		AutoUpdate: false,
		Categories: map[string]config.HomebrewCategory{
			"apps": {Enabled: true, Brewfile: "homebrew/Brewfile.apps"},
		},
	}

	err := tool.Configure(newConfig)
	if err != nil {
		t.Fatalf("Expected Configure to succeed, got: %v", err)
	}

	// Test with invalid config type
	err = tool.Configure("invalid")
	if err == nil {
		t.Fatal("Expected Configure to fail with invalid config type")
	}
}

func TestHomebrewTool_ParseBrewfileLines(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
			DryRun:       true,
		},
		Homebrew: config.HomebrewConfig{
			Categories: map[string]config.HomebrewCategory{
				"test": {Enabled: true, Brewfile: "homebrew/Brewfile.test"},
			},
		},
	}

	tool := NewHomebrewTool(cfg)

	// Create test Brewfile
	brewfileContent := `# Test Brewfile
brew "git"
brew "curl"
cask "visual-studio-code"
tap "homebrew/cask-fonts"
mas "Xcode", id: 497799835

# Comments should be ignored
brew "node" # This package is for development
`

	testutil.CreateTestFile(t, tmpDir, "homebrew/Brewfile.test", brewfileContent)

	brewfilePath := tmpDir + "/homebrew/Brewfile.test"
	items, err := tool.parseBrewfilePackages(brewfilePath, "test")
	if err != nil {
		t.Fatalf("Expected parseBrewfileItems to succeed, got: %v", err)
	}

	if len(items) < 5 {
		t.Errorf("Expected at least 5 items, got %d", len(items))
	}

	// Check that different package types are parsed correctly
	expectedTypes := map[string]string{
		"git":                 "brew",
		"curl":                "brew",
		"visual-studio-code":  "cask",
		"homebrew/cask-fonts": "tap",
		"Xcode":               "mas",
	}

	foundTypes := make(map[string]string)
	for _, item := range items {
		foundTypes[item.Name] = item.PackageType
	}

	for name, expectedType := range expectedTypes {
		if foundType, exists := foundTypes[name]; !exists {
			t.Errorf("Expected to find package %s", name)
		} else if foundType != expectedType {
			t.Errorf("Expected package %s to have type %s, got %s", name, expectedType, foundType)
		}
	}
}

func TestHomebrewTool_SupportsCategories(t *testing.T) {
	cfg := &config.Config{
		Homebrew: config.HomebrewConfig{
			Categories: map[string]config.HomebrewCategory{
				"core": {Enabled: true, Brewfile: "homebrew/Brewfile"},
			},
		},
	}

	tool := NewHomebrewTool(cfg)

	if !tool.SupportsCategories() {
		t.Error("Expected Homebrew tool to support categories")
	}
}

func TestHomebrewTool_GetBrewfileStatus(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
			DryRun:       true,
		},
	}

	tool := NewHomebrewTool(cfg)

	// Create test Brewfile with simple content
	brewfileContent := `brew "git"
cask "visual-studio-code"`

	testutil.CreateTestFile(t, tmpDir, "homebrew/Brewfile.test", brewfileContent)

	// Test reading brewfile status
	brewfilePath := tmpDir + "/homebrew/Brewfile.test"
	total, installed, err := tool.getBrewfileStatus(brewfilePath)
	if err != nil {
		t.Fatalf("Expected getBrewfileStatus to succeed, got: %v", err)
	}

	if total != 2 {
		t.Errorf("Expected total to be 2, got %d", total)
	}

	// installed count will be 0 since we don't have brew installed in test
	if installed < 0 {
		t.Errorf("Expected installed to be non-negative, got %d", installed)
	}
}

func TestHomebrewTool_IsTapInstalled(t *testing.T) {
	cfg := &config.Config{}
	tool := NewHomebrewTool(cfg)

	installedTaps := []string{"homebrew/core", "homebrew/cask", "homebrew/cask-fonts"}

	// Test existing tap
	if !tool.isTapInstalled("homebrew/cask-fonts", installedTaps) {
		t.Error("Expected homebrew/cask-fonts to be detected as installed")
	}

	// Test non-existing tap
	if tool.isTapInstalled("nonexistent/tap", installedTaps) {
		t.Error("Expected nonexistent/tap to be detected as not installed")
	}

	// Test partial match (should not match)
	if tool.isTapInstalled("homebrew/cas", installedTaps) {
		t.Error("Expected homebrew/cas to be detected as not installed (partial match)")
	}
}
