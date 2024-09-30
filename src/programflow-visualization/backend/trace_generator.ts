import { spawn } from 'child_process';
import { dirname } from 'path';
import { MessagePort, isMainThread, parentPort } from 'worker_threads';

export function generateTrace(pythonCmd: string[], mainPath: string, filePath: string, tracePort: MessagePort) {
    if (pythonCmd.length === 0) {
        console.error("Python command is missing");
        tracePort.close();
        return;
    }

    const traceArgs = [mainPath, filePath];
    const args = pythonCmd.slice(1).concat(traceArgs);
    const child = spawn(pythonCmd[0], args, { cwd: dirname(filePath), windowsHide: true });
    let err = "";

    tracePort.on('close', () => {
        child.kill();
    });

    let buffer = Buffer.alloc(0);

    child.stdout.on('data', (data) => {
        buffer = Buffer.concat([buffer, data]);
        while (buffer.length >= 4) {
            const dataLen = buffer.readUint32BE(0);
            if (buffer.length >= 4 + dataLen) {
                const traceStr = buffer.subarray(4, 4 + dataLen).toString();
                try {
                    const traceElem = JSON.parse(traceStr);
                    tracePort.postMessage(traceElem);
                    buffer = buffer.subarray(4 + dataLen);
                } catch (error) {
                    console.error("JSON parsing of trace element failed:", error);
                    tracePort.close();
                    child.kill();
                }
            } else {
                break;
            }
        }
    });
    child.stderr.on('data', (data) => {
        err += data.toString();
    });
    child.on('close', (code) => {
        if (code !== 0) {
            console.error(`trace generator failed with code ${code}: ${err}`);
        }
        tracePort.close();
    });
    child.on('error', (error) => {
        console.error(error);
        tracePort.close();
    });
}

if (!isMainThread && parentPort) {
    parentPort.once('message', (initParams) => {
        generateTrace(initParams.pythonCmd, initParams.mainPath, initParams.file, initParams.tracePort);
    });
}