import { ExtensionContext, OutputChannel, Uri } from 'vscode';
import { MessagePort, Worker } from 'worker_threads';
import { PythonExtension, getPythonCmd } from '../../extension';
import path = require('path');

export function startBackend(context: ExtensionContext, file: Uri, outChannel: OutputChannel): MessagePort {
    const pyExt = new PythonExtension();
    const pythonCmdResult = getPythonCmd(pyExt);
    let pythonCmd = ["python3"];
    switch (pythonCmdResult.kind) {
        case "error":
            outChannel.appendLine(`Getting Python command failed: ${pythonCmdResult.msg}`);
            break;
        case "warning":
            outChannel.appendLine(`Warning while getting Python command: ${pythonCmdResult.msg}`);
            pythonCmd = pythonCmdResult.cmd;
            break;
        case "success":
            pythonCmd = pythonCmdResult.cmd;
            break;
    }

    // Get WYPP path
    const runYourProgramPath = context.asAbsolutePath("python/src/runYourProgram.py");

    const mainPath = context.asAbsolutePath("pytrace-generator/main.py");
    const workerPath = path.resolve(__dirname, 'trace_generator.js');
    const worker = new Worker(workerPath);
    const traceChannel = new MessageChannel();
    const logChannel = new MessageChannel();
    logChannel.port2.on('message', async (logEntry) => outChannel.append(logEntry));
    worker.postMessage({
        file: file.fsPath,
        mainPath: mainPath,
        logPort: logChannel.port1,
        pythonCmd: pythonCmd,
        runYourProgramPath: runYourProgramPath,
        tracePort: traceChannel.port1
    }, [logChannel.port1, traceChannel.port1]);
    return traceChannel.port2;
}
