import { ExtensionContext, Uri } from 'vscode';
import { MessagePort, Worker } from 'worker_threads';
import { PythonExtension, getPythonCmd } from '../../extension';
import path = require('path');

export function startBackend(context: ExtensionContext, file: Uri): MessagePort {
    const pyExt = new PythonExtension();
    const pythonCmdResult = getPythonCmd(pyExt);
    let pythonCmd = ["python3"];
    switch (pythonCmdResult.kind) {
        case "error":
            console.error("Getting Python command failed:", pythonCmdResult.msg);
            break;
        case "warning":
            console.error("Warning while getting Python command:", pythonCmdResult.msg);
            pythonCmd = pythonCmdResult.cmd;
            break;
        case "success":
            pythonCmd = pythonCmdResult.cmd;
            break;
    }

    // Get WYPP path
    const runYourProgramPath = context.asAbsolutePath("python/src/runYourProgram.py");

    const mainPath = context.asAbsolutePath("python/deps/pytrace-generator/main.py");
    const workerPath = path.resolve(__dirname, 'trace_generator.js');
    const worker = new Worker(workerPath);
    const channel = new MessageChannel();
    worker.postMessage({
        file: file.fsPath,
        mainPath: mainPath,
        pythonCmd: pythonCmd,
        runYourProgramPath: runYourProgramPath,
        tracePort: channel.port1
    }, [channel.port1]);
    return channel.port2;
}
