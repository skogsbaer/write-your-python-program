// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

const disposables: vscode.Disposable[] = []

function installButton(title: string, cmd: string) {
	const runButton = vscode.window.createStatusBarItem(1, 0)
	runButton.text = title;
	runButton.color = 'white';
	runButton.command = cmd;
	runButton.show()
	disposables.push(runButton);
}

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	disposables.forEach(d => d.dispose())

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Activating extension write-your-program');
    const helloProg = context.asAbsolutePath('hello.py')
	let terminal: vscode.Terminal;

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	const interpreterCmd = 'write-your-program.PythonInterpreter';
	let interpreter = vscode.commands.registerCommand(interpreterCmd, async () => {
		if (terminal) {
			terminal.dispose();
		}
		terminal = vscode.window.createTerminal({name: "Hello"});
		terminal.show(false); // focus the temrinal
		terminal.sendText("python3 -i " + helloProg);
		// Display a message box to the user
		// vscode.window.showInformationMessage('Hello World from Write Your Program!!');
	});

	disposables.push(interpreter);
	installButton('Start Python Interpreter', interpreterCmd);
	context.subscriptions.push(interpreter);
}

// this method is called when your extension is deactivated
export function deactivate() {
	console.log('Deactivating extension write-your-program');
}
