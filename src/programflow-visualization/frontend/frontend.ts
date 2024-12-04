import { ExtensionContext } from 'vscode';
import { VisualizationPanel } from './visualization_panel';
import { MessagePort } from 'worker_threads';
import * as TraceCache from '../trace_cache';

let panel: VisualizationPanel | undefined = undefined;

export async function startFrontend(
    context: ExtensionContext,
    filePath: string,
    fileHash: string,
    tracePort: MessagePort | null): Promise<Failure | undefined> {
    var trace: BackendTrace = [];
    if (await TraceCache.traceAlreadyExists(context, fileHash)) {
        trace = await TraceCache.getTrace(context, fileHash);
    }

    panel?.dispose();
    panel = await VisualizationPanel.getVisualizationPanel(context, filePath, fileHash, trace, tracePort);
    if (!panel) {
        return failure("Frontend couldn't be initialized!");
    }
}

function failure(errorMessage: string): Failure {
    return { errorMessage: errorMessage } as Failure;
}
