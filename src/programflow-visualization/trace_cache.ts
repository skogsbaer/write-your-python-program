import { Variables } from './constants';
import * as vscode from 'vscode';
import * as tmp from 'tmp';
import path = require('path');
import stringify from 'stringify-json';
import util = require('util');
import * as FileHandler from './FileHandler';

export async function initTraceCache(context: vscode.ExtensionContext): Promise<void> {
    tmp.setGracefulCleanup();
    const tmpDir = tmp.dirSync({ prefix: 'ProgramFlowVisualization', unsafeCleanup: true });
    await setContextState(context, Variables.TRACE_CACHE_DIR, tmpDir.name);

    const cachedTraces: string[] = [];
    await setContextState(context, Variables.CACHED_TRACES, cachedTraces);
    
}

export async function traceAlreadyExists(context: vscode.ExtensionContext, fileHash: string): Promise<boolean> {
    // Check if the hash is contained in cachedTraces, a list of hashes for which a trace already exists
    const cachedTraces: string[] = await getContextState<string[]>(context, Variables.CACHED_TRACES) ?? [];
    return cachedTraces.includes(fileHash);
}

async function getContextState<T>(context: vscode.ExtensionContext, key: string): Promise<T | undefined> {
    return await context.workspaceState.get<T>(key);
}

async function setContextState(context: vscode.ExtensionContext, key: string, value: any): Promise<void> {
    return await context.workspaceState.update(key, value);
}

async function traceCachePath(context: vscode.ExtensionContext, fileHash: string): Promise<string> {
    const cacheDir = await getContextState<string>(context, Variables.TRACE_CACHE_DIR) ?? "";
    return path.join(cacheDir, fileHash + '.json');
}

export async function cacheTrace(context: vscode.ExtensionContext, fileHash: string, trace: BackendTrace) {
    const path = await traceCachePath(context, fileHash);
    await vscode.workspace.fs.writeFile(vscode.Uri.file(path), new util.TextEncoder().encode(stringify(trace)));

    const cachedTraces: string[] = await getContextState<string[]>(context, Variables.CACHED_TRACES) ?? [];
    cachedTraces.push(fileHash);
}

export async function getTrace(context: vscode.ExtensionContext, fileHash: string): Promise<BackendTrace> {
    const path = await traceCachePath(context, fileHash);
    return JSON.parse(await FileHandler.getContentOf(vscode.Uri.file(path)));
}
