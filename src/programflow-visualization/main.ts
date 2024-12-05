import * as vscode from 'vscode';
import { startBackend } from './backend/backend';
import * as FileHandler from './FileHandler';
import { Md5 } from 'ts-md5';
import { startFrontend } from './frontend/frontend';
import { traceAlreadyExists } from './trace_cache';

export function getProgFlowVizCallback(context: vscode.ExtensionContext, outChannel: vscode.OutputChannel): () => Promise<void> {
    return async () => {
        try {
            const file = vscode.window.activeTextEditor ?
                vscode.window.activeTextEditor.document.uri :
                undefined;
            if (!file) {
                vscode.window.showWarningMessage('No file is open');
                return;
            }
            if (!file.fsPath.endsWith('.py')) {
                vscode.window.showWarningMessage('Not a Python file');
                return;
            }
            await vscode.window.activeTextEditor?.document.save();

            const content = await FileHandler.getContentOf(file);
            const fileHash = Md5.hashStr(content);

            let tracePort = null;
            if (!(await traceAlreadyExists(context, fileHash))) {
                tracePort = startBackend(context, file, outChannel);
            }

            const result = await startFrontend(context, file.fsPath, fileHash, tracePort);
            if (result) {
                await vscode.window.showErrorMessage("Error ProgramFlow-Visualization: " + result.errorMessage);
                return;
            }
        } catch (e: any) {
            if (e instanceof Error) {
                outChannel.appendLine(e.stack?.toString() ?? "Error: <stack undefined>");
            } else {
                outChannel.appendLine(e);
            }
            outChannel.show(true);
        }
    };
}
