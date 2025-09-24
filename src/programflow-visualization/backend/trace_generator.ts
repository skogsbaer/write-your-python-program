import { ChildProcessWithoutNullStreams, execFile, ExecFileException, spawn } from 'child_process';
import { AddressInfo, createServer } from 'net';
import { dirname } from 'path';
import { MessagePort, isMainThread, parentPort } from 'worker_threads';

export function generateTrace(pythonCmd: string[], traceGenPath: string, inputFilePath: string, tracePort: MessagePort, logPort: MessagePort) {
    // traceGenPath is something like /Users/swehr/devel/write-your-python-program/pytrace-generator/main.py
    let childRef: ChildProcessWithoutNullStreams[] = [];
    let buffer = Buffer.alloc(0);
    const server = createServer((socket) => {
        socket.on('data', (data) => {
            buffer = Buffer.concat([buffer as Uint8Array, data as Uint8Array]);
            while (buffer.length >= 4) {
                const dataLen = buffer.readUint32BE(0);
                if (buffer.length >= 4 + dataLen) {
                    const traceStr = buffer.subarray(4, 4 + dataLen).toString();
                    try {
                        const traceElem = JSON.parse(traceStr);
                        tracePort.postMessage(traceElem);
                        buffer = buffer.subarray(4 + dataLen);
                    } catch (error) {
                        logPort.postMessage(`JSON parsing of trace element failed: ${error}\n`);
                        tracePort.close();
                        if (childRef.length > 0) {
                            childRef[0].kill();
                        }
                    }
                } else {
                    break;
                }
            }
        });

        socket.on('end', () => {
            tracePort.close();
        });
    });
    server.listen(0, '127.0.0.1', () => {
        const port = (server.address() as AddressInfo)?.port;
        const traceArgs = [traceGenPath, inputFilePath, port.toString()];
        const args = pythonCmd.slice(1).concat(traceArgs);
        const child = spawn(pythonCmd[0], args, {
            cwd: dirname(inputFilePath),
            windowsHide: true
        });
        childRef.push(child);
        let err = "";

        tracePort.on('close', () => {
            child.kill();
            logPort.close();
        });

        child.stdout.on('data', (data) => {
            logPort.postMessage(data.toString());
        });
        child.stderr.on('data', (data) => {
            logPort.postMessage(data.toString());
        });
        child.on('close', (code) => {
            if (code !== 0) {
                logPort.postMessage(`trace generator failed with code ${code}: ${err}\n`);
            }
        });
        child.on('error', (error) => {
            logPort.postMessage(`${error}\n`);
            logPort.close();
            tracePort.close();
        });
    });
}

if (!isMainThread && parentPort) {
    parentPort.once('message', (initParams) => {
        if (initParams.pythonCmd.length === 0) {
            initParams.logPort.postMessage('Python command is missing\n');
            initParams.logPort.close();
            initParams.tracePort.close();
            return;
        }
        generateTrace(initParams.pythonCmd, initParams.mainPath, initParams.file, initParams.tracePort, initParams.logPort);
    });
}
