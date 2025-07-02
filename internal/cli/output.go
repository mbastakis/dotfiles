package cli

import (
	"fmt"
	"os"
	"strings"
	"text/tabwriter"

	"github.com/mbastakis/dotfiles/internal/types"
)

// printStatus prints tool status in a formatted way
func printStatus(status *types.ToolStatus) {
	fmt.Printf("Tool: %s\n", status.Name)
	fmt.Printf("Enabled: %t\n", status.Enabled)
	fmt.Printf("Healthy: %t\n", status.Healthy)

	if status.Error != nil {
		fmt.Printf("Error: %v\n", status.Error)
	}

	if len(status.Items) > 0 {
		fmt.Println("\nItems:")
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintln(w, "NAME\tENABLED\tINSTALLED\tTARGET\tPRIORITY")
		fmt.Fprintln(w, "----\t-------\t---------\t------\t--------")

		for _, item := range status.Items {
			fmt.Fprintf(w, "%s\t%t\t%t\t%s\t%d\n",
				item.Name,
				item.Enabled,
				item.Installed,
				item.Target,
				item.Priority,
			)
		}
		w.Flush()
	}
}

// printItems prints a list of tool items
func printItems(items []types.ToolItem) {
	if len(items) == 0 {
		fmt.Println("No items found")
		return
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "NAME\tENABLED\tINSTALLED\tVERSION\tTARGET")
	fmt.Fprintln(w, "----\t-------\t---------\t-------\t------")

	for _, item := range items {
		version := item.Version
		if version == "" {
			version = "-"
		}

		target := item.Target
		if target == "" {
			target = "-"
		}

		fmt.Fprintf(w, "%s\t%t\t%t\t%s\t%s\n",
			item.Name,
			item.Enabled,
			item.Installed,
			version,
			target,
		)
	}
	w.Flush()
}

// printResult prints operation result
func printResult(result *types.OperationResult) {
	if result.Success {
		fmt.Printf("✅ %s\n", result.Message)
	} else {
		fmt.Printf("❌ %s\n", result.Message)
	}

	if len(result.Modified) > 0 {
		fmt.Printf("Modified: %s\n", strings.Join(result.Modified, ", "))
	}

	if result.Output != "" {
		fmt.Printf("Output:\n%s\n", result.Output)
	}

	if result.Error != nil {
		fmt.Printf("Error: %v\n", result.Error)
	}
}
