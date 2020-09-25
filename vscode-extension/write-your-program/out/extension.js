"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
const vscode = require("vscode");
const disposables = [];
function installButton(title, cmd) {
    const runButton = vscode.window.createStatusBarItem(1, 0);
    runButton.text = title;
    runButton.color = 'white';
    runButton.command = cmd;
    runButton.show();
    disposables.push(runButton);
}
// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
function activate(context) {
    disposables.forEach(d => d.dispose());
    // Use the console to output diagnostic information (console.log) and errors (console.error)
    // This line of code will only be executed once when your extension is activated
    console.log('Activating extension write-your-program');
    const helloProg = context.asAbsolutePath('hello.py');
    let terminal;
    // The command has been defined in the package.json file
    // Now provide the implementation of the command with registerCommand
    // The commandId parameter must match the command field in package.json
    const interpreterCmd = 'write-your-program.PythonInterpreter';
    let interpreter = vscode.commands.registerCommand(interpreterCmd, () => __awaiter(this, void 0, void 0, function* () {
        if (terminal) {
            terminal.dispose();
        }
        terminal = vscode.window.createTerminal({ name: "Hello" });
        terminal.show(false); // focus the temrinal
        terminal.sendText("python3 -i " + helloProg);
        // Display a message box to the user
        // vscode.window.showInformationMessage('Hello World from Write Your Program!!');
    }));
    disposables.push(interpreter);
    installButton('Start Python Interpreter', interpreterCmd);
    context.subscriptions.push(interpreter);
}
exports.activate = activate;
// this method is called when your extension is deactivated
function deactivate() {
    console.log('Deactivating extension write-your-program');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map