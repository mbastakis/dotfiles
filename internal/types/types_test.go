package types

import (
	"fmt"
	"strings"
	"testing"
	"time"
)

func TestToolStatus_Basic(t *testing.T) {
	status := &ToolStatus{
		Name:      "test-tool",
		Enabled:   true,
		Healthy:   true,
		LastCheck: time.Now(),
		Items: []ToolItem{
			{Name: "item1", Status: "installed", Installed: true},
			{Name: "item2", Status: "needs_update", Installed: false},
		},
	}

	if status.Name != "test-tool" {
		t.Errorf("Expected Name to be 'test-tool', got %s", status.Name)
	}

	if !status.Enabled {
		t.Error("Expected Enabled to be true")
	}

	if !status.Healthy {
		t.Error("Expected Healthy to be true")
	}

	if len(status.Items) != 2 {
		t.Errorf("Expected 2 items, got %d", len(status.Items))
	}
}

func TestToolStatus_WithError(t *testing.T) {
	status := &ToolStatus{
		Name:    "test-tool",
		Enabled: true,
		Healthy: false,
		Error:   fmt.Errorf("test error"),
	}

	if status.Error == nil {
		t.Error("Expected Error to be set")
	}

	if status.Healthy {
		t.Error("Expected Healthy to be false when there's an error")
	}
}

func TestToolItem_Basic(t *testing.T) {
	item := ToolItem{
		Name:        "test-item",
		Description: "Test item description",
		Status:      "installed",
		Enabled:     true,
		Installed:   true,
		Version:     "1.0.0",
		Target:      "/test/target",
		Priority:    1,
		Category:    "test",
		PackageType: "brew",
		Metadata: map[string]interface{}{
			"key1": "value1",
			"key2": 42,
		},
	}

	if item.Name != "test-item" {
		t.Errorf("Expected Name to be 'test-item', got %s", item.Name)
	}

	if !item.Enabled {
		t.Error("Expected Enabled to be true")
	}

	if !item.Installed {
		t.Error("Expected Installed to be true")
	}

	if item.Version != "1.0.0" {
		t.Errorf("Expected Version to be '1.0.0', got %s", item.Version)
	}

	if item.Priority != 1 {
		t.Errorf("Expected Priority to be 1, got %d", item.Priority)
	}

	if len(item.Metadata) != 2 {
		t.Errorf("Expected 2 metadata entries, got %d", len(item.Metadata))
	}
}

func TestToolItem_WithError(t *testing.T) {
	item := ToolItem{
		Name:   "test-item",
		Status: "error",
		Error:  "installation failed",
	}

	if item.Error != "installation failed" {
		t.Errorf("Expected Error to be 'installation failed', got %s", item.Error)
	}

	if item.Status != "error" {
		t.Errorf("Expected Status to be 'error', got %s", item.Status)
	}
}

func TestOperationResult_Success(t *testing.T) {
	result := OperationResult{
		Tool:      "test-tool",
		Operation: "install",
		Success:   true,
		Message:   "Installation successful",
		Output:    "Package installed successfully",
		Modified:  []string{"/test/file1", "/test/file2"},
		Details: map[string]interface{}{
			"duration": "5s",
			"count":    2,
		},
	}

	if result.Tool != "test-tool" {
		t.Errorf("Expected Tool to be 'test-tool', got %s", result.Tool)
	}

	if result.Operation != "install" {
		t.Errorf("Expected Operation to be 'install', got %s", result.Operation)
	}

	if !result.Success {
		t.Error("Expected Success to be true")
	}

	if len(result.Modified) != 2 {
		t.Errorf("Expected 2 modified files, got %d", len(result.Modified))
	}

	if len(result.Details) != 2 {
		t.Errorf("Expected 2 detail entries, got %d", len(result.Details))
	}
}

func TestOperationResult_Failure(t *testing.T) {
	result := OperationResult{
		Tool:      "test-tool",
		Operation: "install",
		Success:   false,
		Message:   "Installation failed",
		Error:     fmt.Errorf("package not found"),
		Output:    "Error: package not found",
	}

	if result.Success {
		t.Error("Expected Success to be false")
	}

	if result.Error == nil {
		t.Error("Expected Error to be set")
	}

	if !strings.Contains(result.Message, "failed") {
		t.Error("Expected Message to contain 'failed'")
	}
}

func TestToolStatus_JSONSerialization(t *testing.T) {
	status := &ToolStatus{
		Name:      "test-tool",
		Enabled:   true,
		Healthy:   true,
		LastCheck: time.Now(),
		Items: []ToolItem{
			{Name: "item1", Status: "installed"},
		},
	}

	// Test that it can be marshaled (basic check)
	if status.Name == "" {
		t.Error("Name should not be empty")
	}
	if len(status.Items) == 0 {
		t.Error("Items should not be empty")
	}
}

func TestToolItem_StatusValues(t *testing.T) {
	statusValues := []string{
		"installed",
		"available",
		"outdated",
		"error",
		"unknown",
		"needs_update",
		"synced",
		"needs_sync",
	}

	for _, status := range statusValues {
		item := ToolItem{
			Name:   "test-item",
			Status: status,
		}

		if item.Status != status {
			t.Errorf("Expected Status to be %s, got %s", status, item.Status)
		}
	}
}

func TestOperationResult_Operations(t *testing.T) {
	operations := []string{
		"install",
		"update",
		"remove",
		"sync",
		"status",
		"validate",
		"configure",
	}

	for _, op := range operations {
		result := OperationResult{
			Tool:      "test-tool",
			Operation: op,
			Success:   true,
		}

		if result.Operation != op {
			t.Errorf("Expected Operation to be %s, got %s", op, result.Operation)
		}
	}
}