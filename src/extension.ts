// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import * as process from 'process';
import * as fs from 'fs';
import * as path from 'path';
import { Uri } from 'vscode';

const extensionId = 'write-your-python-program';
const python3ConfigKey = 'python3Cmd';
const verboseConfigKey = 'verbose';
const debugConfigKey = 'debug';
const disableTypecheckingConfigKey = 'disableTypechecking';
const isWindows = process.platform === "win32";
const exeExt = isWindows ? ".exe" : "";

const disposables: vscode.Disposable[] = [];
const buttons: vscode.StatusBarItem[] = [];

function installButton(title: string, cmd: string | undefined) {
    const runButton = vscode.window.createStatusBarItem(1, 0);
    runButton.text = title;
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

function getTerminalConfig(): {shellPath: string | undefined, shellArgs: string | string[] | undefined} {
    const shellConfig = vscode.workspace.getConfiguration('terminal.integrated.shell');
    const shellArgsConfig = vscode.workspace.getConfiguration('terminal.integrated.shellArgs');
    let osSection: string | undefined;
    if (process.platform === "win32") {
        osSection = 'windows';
    } else if (process.platform === "darwin") {
        osSection = 'osx';
    } else if (process.platform === "linux") {
        osSection = 'linux';
    }
    if (osSection) {
        return {
            shellPath: shellConfig.get<string>(osSection) || undefined,
            shellArgs: shellArgsConfig.get<string | string[]>(osSection) || undefined
        };
    } else {
        return {
            shellPath: undefined,
            shellArgs: undefined
        };
    }
}

const POWERSHELLS = [/(powershell.exe$|powershell$)/i, /(pwsh.exe$|pwsh$)/i];

type ShellKind = 'powershell' | 'other';

function identifyShell(shellPath: string): ShellKind {
    for (let pat of POWERSHELLS) {
        if (pat.test(shellPath)) {
            return 'powershell';
        }
    }
    return 'other';
}

async function startTerminal(
    existing: vscode.Terminal | undefined, name: string, cmd: string
): Promise<vscode.Terminal> {
    if (existing) {
        existing.dispose();
    }
    const terminalOptions: vscode.TerminalOptions = {name: name};
    let cmdPrefix = "";
    if (isWindows) {
        const shellCfg = getTerminalConfig();
        const shellPath = shellCfg.shellPath;
        const shellArgs = shellCfg.shellArgs;
        if (shellPath) {
            terminalOptions.shellPath = shellPath;
            if (shellArgs) {
                terminalOptions.shellArgs = shellArgs;
            }
            if (identifyShell(shellPath) === "powershell") {
                cmdPrefix = "& ";
            }
        } else {
            // powershell is the default
            cmdPrefix = "& ";
        }
    }
    const terminal = vscode.window.createTerminal(terminalOptions);
    // Sometimes the terminal takes some time to start up before it can start accepting input.
    await new Promise((resolve) => setTimeout(resolve, 100));
    terminal.show(false); // focus the terminal
    terminal.sendText(cmdPrefix + cmd);
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

function commandListToArgument(arr: string[]): string {
    if (arr.length === 1) {
        return fileToCommandArgument(arr[0]);
    } else {
        var result = "";
        for (let i = 0; i < arr.length; i++) {
            if (i === 0) {
                result = fileToCommandArgument(arr[i]);
            } else {
                result = result + " " + toCommandArgument(arr[i]);
            }
        }
        return result;
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

type PythonCmdResult = {
    kind: "success", cmd: string[]
} | {
    kind: "error", msg: string
} | {
    kind: "warning", msg: string, cmd: string[]
};

function getPythonCmd(ext: PythonExtension): PythonCmdResult {
    const config = vscode.workspace.getConfiguration(extensionId);
    const hasConfig = config && config[python3ConfigKey];
    if (hasConfig) {
        // explicitly configured for wypp (should we deprecate this?)
        let configCmd: string= config[python3ConfigKey];
        configCmd = configCmd.trim();
        if (isWindows && !configCmd.endsWith(exeExt)) {
            configCmd = configCmd + exeExt;
        }
        console.log("Found python command in wypp settings: " + configCmd);
        if (path.isAbsolute(configCmd)) {
            if (fs.existsSync(configCmd)) {
                return {
                    kind: "success",
                    cmd: [configCmd]
                };
            } else {
                return {
                    kind: "error",
                    msg: "Path " + configCmd + " does not exist."
                };
            }
        } else {
            return { kind: 'success', cmd: [configCmd] };
        }
    } else {
        const cmd = ext.getPythonCommand();
        if (cmd) {
            console.log("Using the configured python command " + cmd);
            return {
                kind: 'success',
                cmd
            };
        }
        // The pythonPath configuration has been deprecated, see
        // https://devblogs.microsoft.com/python/python-in-visual-studio-code-july-2021-release/
        const pyConfig = vscode.workspace.getConfiguration("python");
        const pyExtPyPath: string | undefined = pyConfig.get("pythonPath");
        if (pyExtPyPath) {
            console.log("Using python command from pythonPath setting (deprecated): " + pyExtPyPath);
            return {
                kind: 'success',
                cmd: [pyExtPyPath]
            };
        } else {
            const pythonCmd = isWindows ? ('python' + exeExt) : 'python3';
            console.log("Using the default python command: " + pythonCmd);
            return {
                kind: 'success',
                cmd: [pythonCmd]
            };
        }
    }
}

function beVerbose(context: vscode.ExtensionContext): boolean {
    const config = vscode.workspace.getConfiguration(extensionId);
    return !!config[verboseConfigKey];
}

function isDebug(context: vscode.ExtensionContext): boolean {
    const config = vscode.workspace.getConfiguration(extensionId);
    return !!config[debugConfigKey];
}

function disableTypechecking(context: vscode.ExtensionContext): boolean {
    const config = vscode.workspace.getConfiguration(extensionId);
    return !!config[disableTypecheckingConfigKey];
}

function fixPythonConfig(context: vscode.ExtensionContext) {
    const libDir = context.asAbsolutePath('python/src/');
    const pyComplConfig = vscode.workspace.getConfiguration("python.autoComplete");
    const oldPath: string[] = pyComplConfig.get("extraPaths") || [];
    const newPath = oldPath.filter(v => {
        return !v.includes(extensionId);
    });
    if (!newPath.includes(libDir)) {
        newPath.push(libDir);
    }
    pyComplConfig.update("extraPaths", newPath);

    const pyLintConfig = vscode.workspace.getConfiguration("python.linting");
    pyLintConfig.update("enabled", false);
}

class Location implements vscode.TerminalLink {
	constructor(
        public startIndex: number,
        public length: number,
        public tooltip: string | undefined,
        public filePath: string,
        public line: number
    ) { }
}

const linkPrefixes = ['declared at: ', 'caused by: '];

function findLink(dir: string, ctxLine: string): Location | undefined {
    for (const pref of linkPrefixes) {
        if (ctxLine.startsWith(pref)) {
            const link = ctxLine.substr(pref.length).trim();
            const i = link.indexOf(':');
            if (i < 0 || i >= link.length - 1) {
                return undefined;
            }
            const file = link.substr(0, i);
            const line = parseInt(link.substr(i + 1));
            if (file && file.length > 1 && !isNaN(line)) {
                const p = path.join(dir, file);
                const loc = new Location(pref.length, link.length, undefined, p, line);
                // console.debug("Find link " + p + ":" + line);
                return loc;
            } else {
                return undefined;
            }
        }
    }
    return undefined;
}

interface TerminalContext {
    directory: string,
    terminal: vscode.Terminal
}

type TerminalMap = { [name: string]: TerminalContext };

class TerminalLinkProvider implements vscode.TerminalLinkProvider {

	constructor(private terminals: TerminalMap) {}

	provideTerminalLinks(context: vscode.TerminalLinkContext, token: vscode.CancellationToken): vscode.ProviderResult<Location[]> {
        let directory: string | undefined;
        for (const [_key, term] of Object.entries(this.terminals)) {
            if (context.terminal === term.terminal) {
                directory = term.directory;
                break;
            }
        }
        if (directory === undefined) {
            return [];
        }
        const loc = findLink(directory, context.line);
        if (loc) {
            return [loc];
        } else {
            return [];
        }
	}
	handleTerminalLink(loc: Location): vscode.ProviderResult<void> {
		console.log("Opening " + loc.filePath);

		vscode.commands.executeCommand('vscode.open', Uri.file(loc.filePath)).then(() => {
			const editor = vscode.window.activeTextEditor;
			if (!editor) { return; }
			let line = loc.line - 1;
			if (line < 0) {
				line = 0;
			}
			const col = 0;
			editor.selection = new vscode.Selection(line, col, line, col);
			editor.revealRange(new vscode.Range(line, 0, line, 10000));
		});
	}
}

class PythonExtension {
    private pyApi: any;

    constructor() {
        const pyExt = vscode.extensions.getExtension('ms-python.python');
        this.pyApi = pyExt?.exports;
    }

    getPythonCommand(): string[] | undefined {
        return this.pyApi?.settings?.getExecutionDetails()?.execCommand;
    }
}

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
    disposables.forEach(d => d.dispose());

    console.log('Activating extension ' + extensionId);

    fixPythonConfig(context);
    const terminals: { [name: string]: TerminalContext } = {};

    installButton("Write Your Python Program", undefined);

    const linkProvider = new TerminalLinkProvider(terminals);
    const pyExt = new PythonExtension();

    // Run
    const runProg = context.asAbsolutePath('python/src/runYourProgram.py');
    installCmd(
        context,
        "run",
        "▶ RUN",
        async (cmdId) => {
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
            const pyCmd = getPythonCmd(pyExt);
            let verboseOpt = "";
            if (isDebug(context)) {
                verboseOpt = "--debug";
            } else if (beVerbose(context)) {
                verboseOpt = "--verbose";
            }
            if (verboseOpt !== "") {
                verboseOpt = " " + verboseOpt + " --no-clear";
            }
            const disableOpt = disableTypechecking(context) ? " --no-typechecking" : "";
            if (pyCmd.kind !== "error") {
                const pythonCmd = commandListToArgument(pyCmd.cmd);
                const cmdTerm = await startTerminal(
                    terminals[cmdId]?.terminal,
                    "WYPP - RUN",
                    pythonCmd +  " " + fileToCommandArgument(runProg) + verboseOpt +
                        disableOpt +
                        " --install-mode install" +
                        " --interactive " +
                        " --change-directory " +
                        fileToCommandArgument(file)
                );
                terminals[cmdId] = {terminal: cmdTerm, directory: path.dirname(file)};
                if (pyCmd.kind === "warning") {
                    vscode.window.showInformationMessage(pyCmd.msg);
                }
            } else {
                vscode.window.showWarningMessage(pyCmd.msg);
            }
        }
    );

    vscode.window.onDidChangeActiveTextEditor(showHideButtons);
    showHideButtons(vscode.window.activeTextEditor);

    const linkDisposable = vscode.window.registerTerminalLinkProvider(linkProvider);
    disposables.push(linkDisposable);
    context.subscriptions.push(linkDisposable);
}

// this method is called when your extension is deactivated
export function deactivate() {
    console.log('Deactivating extension write-your-program');
    disposables.forEach(d => d.dispose());
    buttons.splice(0, buttons.length);
    disposables.splice(0, disposables.length);
}
