import * as vscode from 'vscode';

interface TuiApp {
    name: string;
    command: string;
    terminalName: string;
}

const TUI_APPS: { [key: string]: TuiApp } = {
    lazygit: {
        name: 'lazygit',
        command: 'lazygit && exit',
        terminalName: 'Lazygit'
    },
    lazydocker: {
        name: 'lazydocker',
        command: 'lazydocker && exit',
        terminalName: 'Lazydocker'
    },
    yazi: {
        name: 'yazi',
        command: 'y && exit',
        terminalName: 'Yazi'
    },
    btop: {
        name: 'btop',
        command: 'btop && exit',
        terminalName: 'Btop'
    },
    k9s: {
        name: 'k9s',
        command: 'k9s && exit',
        terminalName: 'K9s'
    },
    opencode: {
        name: 'opencode',
        command: 'opencode && exit',
        terminalName: 'Opencode'
    },
    basicterminal: {
        name: 'basicterminal',
        command: '',
        terminalName: 'Basic Terminal'
    }
};

class TuiManager {
    private terminals: Map<string, vscode.Terminal> = new Map();

    async openTuiApp(appKey: string): Promise<void> {
        const app = TUI_APPS[appKey];
        if (!app) {
            vscode.window.showErrorMessage(`Unknown TUI app: ${appKey}`);
            return;
        }

        // Look for existing terminal with this name
        let existingTerminal = this.terminals.get(appKey);

        // Check if the terminal still exists (user might have closed it)
        if (existingTerminal) {
            // Try to find it in the current terminals
            const allTerminals = vscode.window.terminals;
            const stillExists = allTerminals.some(t => t === existingTerminal);
            
            if (!stillExists) {
                // Terminal was closed, remove from our map
                this.terminals.delete(appKey);
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
            this.terminals.set(appKey, terminal);
            
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

    // Register commands for each TUI app
    const commands = [
        vscode.commands.registerCommand('tui-manager.openBasicTerminal', () => tuiManager.openTuiApp('basicterminal')),
        vscode.commands.registerCommand('tui-manager.openLazygit', () => tuiManager.openTuiApp('lazygit')),
        vscode.commands.registerCommand('tui-manager.openLazydocker', () => tuiManager.openTuiApp('lazydocker')),
        vscode.commands.registerCommand('tui-manager.openYazi', () => tuiManager.openTuiApp('yazi')),
        vscode.commands.registerCommand('tui-manager.openBtop', () => tuiManager.openTuiApp('btop')),
        vscode.commands.registerCommand('tui-manager.openK9s', () => tuiManager.openTuiApp('k9s')),
        vscode.commands.registerCommand('tui-manager.openOpencode', () => tuiManager.openTuiApp('opencode')),
    ];

    // Add all commands to the extension context
    commands.forEach(command => context.subscriptions.push(command));
}

export function deactivate() {}
