import * as vscode from 'vscode';

interface TuiApp {
    id: string;
    name: string;
    command: string;
    terminalName: string;
}

class TuiManager {
    private terminals: Map<string, vscode.Terminal> = new Map();

    async openTuiApp(app: TuiApp): Promise<void> {
        // Look for existing terminal with this app id
        let existingTerminal = this.terminals.get(app.id);

        // Check if the terminal still exists (user might have closed it)
        if (existingTerminal) {
            // Try to find it in the current terminals
            const allTerminals = vscode.window.terminals;
            const stillExists = allTerminals.some(t => t === existingTerminal);
            
            if (!stillExists) {
                // Terminal was closed, remove from our map
                this.terminals.delete(app.id);
                existingTerminal = undefined;
            }
        }

        if (existingTerminal) {
            // Focus existing terminal - use both show() and reveal for better focus
            existingTerminal.show();
            // Small delay to ensure proper focus
            setTimeout(() => {
                if (existingTerminal) {
                    existingTerminal.show();
                }
            }, 50);
        } else {
            // Create new terminal in editor area
            const terminal = vscode.window.createTerminal({
                name: app.terminalName,
                location: vscode.TerminalLocation.Editor
            });
            
            // Store reference
            this.terminals.set(app.id, terminal);
            
            // Show terminal first
            terminal.show();
            
            // Only send command if it's not empty (for basic terminal)
            if (app.command.trim() !== '') {
                terminal.sendText(app.command);
            }
        }
    }
}

export function activate(context: vscode.ExtensionContext) {
    const tuiManager = new TuiManager();
    
    // Register commands based on current configuration
    registerCommandsFromConfig(context, tuiManager);

    // Listen for configuration changes
    const configListener = vscode.workspace.onDidChangeConfiguration(event => {
        if (event.affectsConfiguration('tuiManager.apps')) {
            // Re-register commands when configuration changes
            registerCommandsFromConfig(context, tuiManager);
        }
    });

    context.subscriptions.push(configListener);
}

function registerCommandsFromConfig(context: vscode.ExtensionContext, tuiManager: TuiManager) {
    // Get TUI apps from configuration
    const config = vscode.workspace.getConfiguration('tuiManager');
    const apps: TuiApp[] = config.get('apps', []);

    // Register a command for each configured TUI app
    apps.forEach(app => {
        const commandId = `tui-manager.${app.id}`;
        
        const disposable = vscode.commands.registerCommand(commandId, () => {
            tuiManager.openTuiApp(app);
        });

        context.subscriptions.push(disposable);
    });

    // Show a status message about registered apps (optional)
    if (apps.length > 0) {
        console.log(`TUI Manager: Registered ${apps.length} TUI applications`);
    }
}

export function deactivate() {}