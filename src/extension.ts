// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import * as process from 'process';
import * as fs from 'fs';
import * as path from 'path';
import { Uri } from 'vscode';

import { getProgFlowVizCallback } from './programflow-visualization/main';
import { initTraceCache } from './programflow-visualization/trace_cache';

const extensionId = 'write-your-python-program';
const python3ConfigKey = 'python3Cmd';
const verboseConfigKey = 'verbose';
const debugConfigKey = 'debug';
const languageKey = 'language';
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

async function startTerminal(
    existing: vscode.Terminal | undefined, name: string, cmd: string
): Promise<vscode.Terminal> {
    let terminal: vscode.Terminal | undefined;
    if (existing) {
        // We try to re-use the existing terminal. But we need to terminate a potentially
        // running python process first. If there is no python process, the shell
        // complains about the "import sys; sys.exit(0)" command, but we don't care.
        if (!existing.exitStatus) {
            terminal = existing;
            terminal.sendText("import sys; sys.exit(0)");
        } else {
            existing.dispose();
        }
    }
    if (!terminal) {
         const terminalOptions: vscode.TerminalOptions = {name: name};
        if (isWindows) {
            // We don't know which shell will be used by default.
            // If PowerShell is the default, we need to prefix the command with "& ".
            // Otherwise, the prefix is not allowed and results in a syntax error.
            // -> Just force cmd.exe.
            terminalOptions.shellPath = "cmd.exe";
        }
        terminal = vscode.window.createTerminal(terminalOptions);
        // Sometimes the terminal takes some time to start up before it can start accepting input.
        await new Promise((resolve) => setTimeout(resolve, 100));
    }
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

function initProgramFlowVisualization(context: vscode.ExtensionContext, outChannel: vscode.OutputChannel) {
    initTraceCache(context);
    const cmdId = extensionId + ".programflow-visualization";
    let disposable = vscode.commands.registerCommand(cmdId, getProgFlowVizCallback(context, outChannel));
    disposables.push(disposable);
    context.subscriptions.push(disposable);
    installButton("$(debug-alt-small) Visualize", cmdId);
}

type PythonCmdResult = {
    kind: "success", cmd: string[]
} | {
    kind: "error", msg: string
} | {
    kind: "warning", msg: string, cmd: string[]
};

export function getPythonCmd(ext: PythonExtension): PythonCmdResult {
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

function getLanguage(context: vscode.ExtensionContext): 'en' | 'de' | undefined {
    const config = vscode.workspace.getConfiguration(extensionId);
    const lang = config[languageKey];
    if (lang === 'english') {
        return 'en';
    } else if (lang === 'german') {
        return 'de';
    } else {
        return undefined;
    }
}


async function fixPylanceConfig(
    context: vscode.ExtensionContext,
    folder?: vscode.WorkspaceFolder
) {
    // disable warnings about wildcard imports, set pylance's extraPaths to wypp
    // turn typechecking off
    // This is a quite distructive change, so we do it on first hit of the run button
    // not on-load of the plugin
    const subDir = 'python/code';
    const libDir = context.asAbsolutePath(subDir);

    const cfg = vscode.workspace.getConfiguration('python', folder?.uri);
    const target = folder ? vscode.ConfigurationTarget.WorkspaceFolder
                   : vscode.ConfigurationTarget.Workspace;

    const errors: string[] = [];

    // Two special errors
    const noWorkspaceOpen = '__NO_WORKSPACE_OPEN__';

    // helper to update config and collect errors; treat "no folder open" specially
    async function tryUpdate(key: string, value: any) {
        // If target is workspace-wide and there is no workspace open at all
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            // nothing to update at workspace level
            errors.push(noWorkspaceOpen);
            return;
        }

        try {
            await cfg.update(key, value, target);
        } catch (e) {
            // If the error message explicitly mentions the workspace/folder, capture it, but prefer the proactive checks above
            const msg = e instanceof Error ? e.message : String(e);
            errors.push(`Failed to update ${key}: ${msg}`);
        }
    }

    // wildcard warnings
    const keyOverride = 'analysis.diagnosticSeverityOverrides';
    const overrides = cfg.get<Record<string, string>>(keyOverride) ?? {};
    if (overrides.reportWildcardImportFromLibrary !== 'none') {
        const updated = {
            ...overrides,
            reportWildcardImportFromLibrary: 'none',
        };
        await tryUpdate(keyOverride, updated);
    }

    // extraPaths
    const keyExtraPaths = 'analysis.extraPaths';
    const extra = cfg.get<string[]>(keyExtraPaths) ?? [];
    // Filter out old plugin paths (paths containing 'write-your-python-program' but not matching current libDir)
    const filtered = extra.filter(p => {
        const isPluginPath = p.includes('stefanwehr.write-your-python-program') && p.includes(subDir);
        return !isPluginPath;
    });
    if (!filtered.includes(libDir)) {
        const newExtra = [...filtered, libDir];
        await tryUpdate(keyExtraPaths, newExtra);
    } else if (filtered.length !== extra.length) {
        // libDir is already present but we removed old paths, so update anyway
        await tryUpdate(keyExtraPaths, filtered);
    }

    // typechecking off
    const keyMode = 'analysis.typeCheckingMode';
    const mode = cfg.get<string>(keyMode) ?? '';
    if (mode !== 'off') {
        await tryUpdate(keyMode, 'off');
    }

    if (errors.length > 0) {
        let msg: string;
        if (errors.every(e => e === noWorkspaceOpen)) {
            msg = 'Write Your Python Program: settings were not changed because no folder is open. Open a folder to apply wypp settings.';
        } else {
            const sanitized = errors.map(e => e === noWorkspaceOpen ? 'Skipped workspace update because no folder is open' : e);
            msg = `Write Your Python Program: failed to update settings. ` + sanitized.join('. ');
        }
        try {
            vscode.window.showWarningMessage(msg);
        } catch (_e) {
            // ignore any error while showing the warning
        }
    }
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

export class PythonExtension {
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
export async function activate(context: vscode.ExtensionContext) {
    disposables.forEach(d => d.dispose());

    console.log('Activating extension ' + extensionId);

    const outChannel = vscode.window.createOutputChannel("Write Your Python Program");
    disposables.push(outChannel);

    const terminals: { [name: string]: TerminalContext } = {};
    vscode.window.onDidCloseTerminal((t) => {
        // Loop through terminals and delete the entry if it matches the closed terminal
        for (const [key, termContext] of Object.entries(terminals)) {
            if (termContext.terminal === t) {
                delete terminals[key];
                console.log(`Terminal closed and removed from map: ${t.name} (key: ${key})`);
                break;
            }
        }
    });

    installButton("Write Your Python Program", undefined);

    const linkProvider = new TerminalLinkProvider(terminals);
    const pyExt = new PythonExtension();
    const runProg = context.asAbsolutePath('python/code/wypp/runYourProgram.py');

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
            await fixPylanceConfig(context);
            await vscode.window.activeTextEditor?.document.save();
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
            const lang = getLanguage(context);
            let langOpt = "";
            if (lang) {
                langOpt = " --lang " + lang;
            }
            const disableOpt = disableTypechecking(context) ? " --no-typechecking" : "";
            if (pyCmd.kind !== "error") {
                const pythonCmd = commandListToArgument(pyCmd.cmd);
                const cmdTerm = await startTerminal(
                    terminals[cmdId]?.terminal,
                    "WYPP - RUN",
                    pythonCmd +  " " + fileToCommandArgument(runProg) + verboseOpt +
                        disableOpt + langOpt +
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

    initProgramFlowVisualization(context, outChannel);

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
