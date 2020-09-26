// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

const extensionId = 'write-your-python-program';
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

function quote(s: string) {
	if (s.match("[ \\t'\"]")) {
		return JSON.stringify(s);
	} else {
		return s;
	}
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

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	disposables.forEach(d => d.dispose());

	console.log('Activating extension ' + extensionId);

	const pythonCmd = quote('python3'); // make configurable
	const terminals: { [name: string]: vscode.Terminal } = {};

	installButton("Write Your Python Program:", undefined);

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
			terminals[cmdId] = startTerminal(
				terminals[cmdId],
				"RUN",
			    pythonCmd + " -i " + quote(runProg) + " " + quote(file)
			);
		}
	);

	// Interpreter
	installCmd(
		context,
		"interpreter",
		"🐍 Interpreter",
		() => {
			terminals["interpreter"] = startTerminal(
				terminals["interpreter"],
				"Interpreter",
				pythonCmd + " -i"
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
