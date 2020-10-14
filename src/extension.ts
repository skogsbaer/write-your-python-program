// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import * as process from 'process';
import * as fs from 'fs';
import * as path from 'path';

const extensionId = 'write-your-python-program';
const python3ConfigKey = 'python3Cmd';
const isWindows = process.platform === "win32";
const exeExt = isWindows ? ".exe" : "";

const disposables: vscode.Disposable[] = [];
const buttons: vscode.StatusBarItem[] = [];

function installButton(title: string, cmd: string | undefined) {
    const runButton = vscode.window.createStatusBarItem(1, 0);
    runButton.text = title;
    runButton.color = 'white';
    if (cmd) {
        runButton.command = cmd;
    }
    buttons.push(runButton);
    disposables.push(runButton);
}

function hideButtons() {
    buttons.forEach(b => {
        b.hide();
    });
}

function showButtons() {
    buttons.forEach(b => {
        b.show();
    });
}

function startTerminal(
    existing: vscode.Terminal | undefined, name: string, cmd: string
): vscode.Terminal {
    if (existing) {
        existing.dispose();
    }
    const terminal = vscode.window.createTerminal({name: name});
    terminal.show(false); // focus the terminal
    terminal.sendText(cmd);
    return terminal;
}

/**
 * Appropriately formats a string so it can be used as an argument for a command in a shell.
 * E.g. if an argument contains a space, then it will be enclosed within double quotes.
 * @param {String} value.
 */
function toCommandArgument(s: string): string {
    if (!s) {
        return s;
    }
    return s.indexOf(' ') >= 0 && !s.startsWith('"') && !s.endsWith('"') ? `"${s}"` : s.toString();
};

/**
 * Appropriately formats a a file path so it can be used as an argument for a command in a shell.
 * E.g. if an argument contains a space, then it will be enclosed within double quotes.
 */
function fileToCommandArgument(s: string): string {
    if (!s) {
        return s;
    }
    return toCommandArgument(s).replace(/\\/g, '/');
}

function showHideButtons(textEditor: vscode.TextEditor | undefined) {
    if (!textEditor) {
        hideButtons();
        return;
    }
    const fileName = textEditor.document.fileName;
    if (fileName.endsWith('.py')) {
        showButtons();
    } else {
        hideButtons();
    }
}

function installCmd(
    context: vscode.ExtensionContext,
    cmdId: string,
    buttonTitle: string,
    callback: (cmdId: string) => void
) {
    cmdId = extensionId + "." + cmdId;
    let disposable = vscode.commands.registerCommand(cmdId, () => callback(cmdId));
    disposables.push(disposable);
    context.subscriptions.push(disposable);
    installButton(buttonTitle, cmdId);
}

function getPythonCmd(): string {
    const config = vscode.workspace.getConfiguration()[extensionId];
    let pythonCmds = ['python3' + exeExt, 'python' + exeExt];
    if (config && config[python3ConfigKey]) {
        pythonCmds = [config[python3ConfigKey]];
    }
    for (let cmd of pythonCmds) {
        if (fs.existsSync(cmd)) {
            return cmd;
        }
    }
    const p = process.env.PATH;
    const pComps = p ? p.split(path.delimiter) : [];
    for (let cmd of pythonCmds) {
        for (let comp of pComps) {
            const fullP = path.join(comp, cmd);
            if (fs.existsSync(fullP)) {
                return fullP;
            }
        }
    }
    return isWindows ? ("python" + exeExt) : ("python3" + exeExt); // just hope the best
}

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
    disposables.forEach(d => d.dispose());

    console.log('Activating extension ' + extensionId);

    const terminals: { [name: string]: vscode.Terminal } = {};

    installButton("Write Your Python Program", undefined);

    // Run
    const runProg = context.asAbsolutePath('python/src/runYourProgram.py');
    installCmd(
        context,
        "run",
        "▶ RUN",
        (cmdId) => {
            const file =
                (vscode.window.activeTextEditor) ?
                vscode.window.activeTextEditor.document.fileName :
                undefined;
            if (!file) {
                vscode.window.showWarningMessage('No file is open');
                return;
            }
            if (!file.endsWith('.py')) {
                vscode.window.showWarningMessage('Not a python file');
                return;
            }
            vscode.window.activeTextEditor?.document.save();
            const pythonCmd = fileToCommandArgument(getPythonCmd());
            terminals[cmdId] = startTerminal(
                terminals[cmdId],
                "WYPP - RUN",
                pythonCmd + " -i " + fileToCommandArgument(runProg) + " " + fileToCommandArgument(file)
            );
        }
    );

    vscode.window.onDidChangeActiveTextEditor(showHideButtons);
    showHideButtons(vscode.window.activeTextEditor);
}

// this method is called when your extension is deactivated
export function deactivate() {
    console.log('Deactivating extension write-your-program');
    disposables.forEach(d => d.dispose());
    buttons.splice(0, buttons.length);
    disposables.splice(0, disposables.length);
}
