import { ExtensionContext, Uri } from 'vscode';
import { MessagePort, Worker } from 'worker_threads';
import path = require('path');

export function startBackend(context: ExtensionContext, file: Uri): MessagePort {
    const mainPath = context.asAbsolutePath("python/deps/pytrace-generator/main.py");
    const workerPath = path.resolve(__dirname, 'trace_generator.js');
    const worker = new Worker(workerPath);
    const channel = new MessageChannel();
    worker.postMessage({
        file: file.fsPath,
        mainPath: mainPath,
        tracePort: channel.port1
    }, [channel.port1]);
    return channel.port2;
}
