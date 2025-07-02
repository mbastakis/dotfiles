package keys

import (
	"testing"
)

func TestDefaultToolKeyMap(t *testing.T) {
	keyMap := DefaultToolKeyMap()

	// Test Install binding
	if len(keyMap.Install.Keys()) == 0 {
		t.Error("Expected Install binding to have keys")
	}
	if keyMap.Install.Keys()[0] != "i" {
		t.Errorf("Expected Install key to be 'i', got %s", keyMap.Install.Keys()[0])
	}

	// Test Update binding
	if len(keyMap.Update.Keys()) == 0 {
		t.Error("Expected Update binding to have keys")
	}
	if keyMap.Update.Keys()[0] != "u" {
		t.Errorf("Expected Update key to be 'u', got %s", keyMap.Update.Keys()[0])
	}

	// Test Remove binding
	if len(keyMap.Remove.Keys()) == 0 {
		t.Error("Expected Remove binding to have keys")
	}
	if keyMap.Remove.Keys()[0] != "d" {
		t.Errorf("Expected Remove key to be 'd', got %s", keyMap.Remove.Keys()[0])
	}

	// Test Sync binding
	if len(keyMap.Sync.Keys()) == 0 {
		t.Error("Expected Sync binding to have keys")
	}
	if keyMap.Sync.Keys()[0] != "s" {
		t.Errorf("Expected Sync key to be 's', got %s", keyMap.Sync.Keys()[0])
	}

	// Test Refresh binding
	if len(keyMap.Refresh.Keys()) == 0 {
		t.Error("Expected Refresh binding to have keys")
	}
	if keyMap.Refresh.Keys()[0] != "r" {
		t.Errorf("Expected Refresh key to be 'r', got %s", keyMap.Refresh.Keys()[0])
	}

	// Test Select binding (has multiple keys)
	if len(keyMap.Select.Keys()) < 2 {
		t.Error("Expected Select binding to have at least 2 keys")
	}
	expectedSelectKeys := []string{" ", "x"}
	for i, expectedKey := range expectedSelectKeys {
		if i >= len(keyMap.Select.Keys()) || keyMap.Select.Keys()[i] != expectedKey {
			t.Errorf("Expected Select key %d to be '%s', got %s", i, expectedKey, keyMap.Select.Keys()[i])
		}
	}

	// Test Back binding (has multiple keys)
	if len(keyMap.Back.Keys()) < 2 {
		t.Error("Expected Back binding to have at least 2 keys")
	}
	expectedBackKeys := []string{"q", "esc"}
	for i, expectedKey := range expectedBackKeys {
		if i >= len(keyMap.Back.Keys()) || keyMap.Back.Keys()[i] != expectedKey {
			t.Errorf("Expected Back key %d to be '%s', got %s", i, expectedKey, keyMap.Back.Keys()[i])
		}
	}

	// Test Help binding
	if len(keyMap.Help.Keys()) == 0 {
		t.Error("Expected Help binding to have keys")
	}
}

func TestDefaultNavigationKeyMap(t *testing.T) {
	keyMap := DefaultNavigationKeyMap()

	// Test Up binding
	if len(keyMap.Up.Keys()) == 0 {
		t.Error("Expected Up binding to have keys")
	}
	expectedUpKeys := []string{"up", "k"}
	for i, expectedKey := range expectedUpKeys {
		if i >= len(keyMap.Up.Keys()) || keyMap.Up.Keys()[i] != expectedKey {
			t.Errorf("Expected Up key %d to be '%s', got %s", i, expectedKey, keyMap.Up.Keys()[i])
		}
	}

	// Test Down binding
	if len(keyMap.Down.Keys()) == 0 {
		t.Error("Expected Down binding to have keys")
	}
	expectedDownKeys := []string{"down", "j"}
	for i, expectedKey := range expectedDownKeys {
		if i >= len(keyMap.Down.Keys()) || keyMap.Down.Keys()[i] != expectedKey {
			t.Errorf("Expected Down key %d to be '%s', got %s", i, expectedKey, keyMap.Down.Keys()[i])
		}
	}

	// Test Enter binding
	if len(keyMap.Enter.Keys()) == 0 {
		t.Error("Expected Enter binding to have keys")
	}
	if keyMap.Enter.Keys()[0] != "enter" {
		t.Errorf("Expected Enter key to be 'enter', got %s", keyMap.Enter.Keys()[0])
	}

	// Test Tab binding
	if len(keyMap.Tab.Keys()) == 0 {
		t.Error("Expected Tab binding to have keys")
	}
	if keyMap.Tab.Keys()[0] != "tab" {
		t.Errorf("Expected Tab key to be 'tab', got %s", keyMap.Tab.Keys()[0])
	}

	// Test Quit binding
	if len(keyMap.Quit.Keys()) == 0 {
		t.Error("Expected Quit binding to have keys")
	}
	if keyMap.Quit.Keys()[0] != "ctrl+c" {
		t.Errorf("Expected Quit key to be 'ctrl+c', got %s", keyMap.Quit.Keys()[0])
	}
}

func TestKeyBindingHelp(t *testing.T) {
	keyMap := DefaultToolKeyMap()

	// Test that help messages are not empty
	installHelp := keyMap.Install.Help()
	if installHelp.Key == "" || installHelp.Desc == "" {
		t.Error("Expected Install binding to have non-empty help")
	}

	updateHelp := keyMap.Update.Help()
	if updateHelp.Key == "" || updateHelp.Desc == "" {
		t.Error("Expected Update binding to have non-empty help")
	}

	syncHelp := keyMap.Sync.Help()
	if syncHelp.Key == "" || syncHelp.Desc == "" {
		t.Error("Expected Sync binding to have non-empty help")
	}
}

func TestKeyBindingEnabled(t *testing.T) {
	keyMap := DefaultToolKeyMap()

	// Test that bindings are enabled by default
	if !keyMap.Install.Enabled() {
		t.Error("Expected Install binding to be enabled")
	}
	if !keyMap.Update.Enabled() {
		t.Error("Expected Update binding to be enabled")
	}
	if !keyMap.Sync.Enabled() {
		t.Error("Expected Sync binding to be enabled")
	}
}

func TestToolKeyMapHelp(t *testing.T) {
	keyMap := DefaultToolKeyMap()

	// Test ShortHelp
	shortHelp := keyMap.ShortHelp()
	if len(shortHelp) == 0 {
		t.Error("Expected ShortHelp to return non-empty slice")
	}

	expectedShortHelpCount := 5 // Refresh, Install, Update, Sync, Back
	if len(shortHelp) != expectedShortHelpCount {
		t.Errorf("Expected ShortHelp to return %d bindings, got %d", expectedShortHelpCount, len(shortHelp))
	}

	// Test FullHelp
	fullHelp := keyMap.FullHelp()
	if len(fullHelp) == 0 {
		t.Error("Expected FullHelp to return non-empty slice")
	}

	expectedFullHelpGroups := 3 // Three groups of bindings
	if len(fullHelp) != expectedFullHelpGroups {
		t.Errorf("Expected FullHelp to return %d groups, got %d", expectedFullHelpGroups, len(fullHelp))
	}

	// Check that each group has bindings
	for i, group := range fullHelp {
		if len(group) == 0 {
			t.Errorf("Expected FullHelp group %d to have bindings", i)
		}
	}
}

func TestNavigationKeyMapHelp(t *testing.T) {
	keyMap := DefaultNavigationKeyMap()

	// Test that help messages exist for navigation keys
	upHelp := keyMap.Up.Help()
	if upHelp.Key == "" || upHelp.Desc == "" {
		t.Error("Expected Up binding to have non-empty help")
	}

	downHelp := keyMap.Down.Help()
	if downHelp.Key == "" || downHelp.Desc == "" {
		t.Error("Expected Down binding to have non-empty help")
	}

	enterHelp := keyMap.Enter.Help()
	if enterHelp.Key == "" || enterHelp.Desc == "" {
		t.Error("Expected Enter binding to have non-empty help")
	}

	quitHelp := keyMap.Quit.Help()
	if quitHelp.Key == "" || quitHelp.Desc == "" {
		t.Error("Expected Quit binding to have non-empty help")
	}
}
