// Terminates a program started by the RUN button that is still running, together
// with all processes it started. The python runner writes its process ID (and on
// Unix its process group) to a PID file and keeps the file open until it exits
// (see python/code/wypp/pidFile.py).

import { execFile } from 'child_process';
import * as fs from 'fs';

const isWindows = process.platform === 'win32';

interface PidFileContent {
    pid: number,
    pgid: number | null
}

function run(cmd: string, args: string[]): Promise<{ ok: boolean, stdout: string }> {
    return new Promise((resolve) => {
        execFile(cmd, args, { windowsHide: true }, (err, stdout) => {
            resolve({ ok: !err, stdout: stdout ?? '' });
        });
    });
}

function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function isAlive(pid: number): boolean {
    try {
        process.kill(pid, 0);
        return true;
    } catch (e) {
        // EPERM: the process exists but belongs to someone else
        return (e as NodeJS.ErrnoException).code === 'EPERM';
    }
}

function tryUnlink(file: string): NodeJS.ErrnoException | undefined {
    try {
        fs.unlinkSync(file);
        return undefined;
    } catch (e) {
        return e as NodeJS.ErrnoException;
    }
}

function readPidFile(pidFile: string): PidFileContent | undefined {
    let content: string;
    try {
        content = fs.readFileSync(pidFile, 'utf-8');
    } catch (e) {
        return undefined;
    }
    try {
        const json = JSON.parse(content);
        if (typeof json.pid === 'number') {
            return { pid: json.pid, pgid: typeof json.pgid === 'number' ? json.pgid : null };
        }
    } catch (e) {
        // fall through
    }
    return undefined;
}

async function killOnWindows(pidFile: string, info: PidFileContent, log: (s: string) => void) {
    // The runner keeps the PID file open, and an open file cannot be deleted on Windows.
    // If deleting succeeds, the runner is gone.
    const err = tryUnlink(pidFile);
    if (!err || err.code === 'ENOENT') {
        log('PID file was stale, no program to terminate');
        return;
    }
    log(`Terminating process ${info.pid} and its children`);
    // /T: also kill all child processes, /F: force
    const res = await run('taskkill', ['/PID', String(info.pid), '/T', '/F']);
    if (!res.ok) {
        log(`taskkill failed for process ${info.pid}`);
    }
    // The handle of the PID file is released shortly after the process has died.
    for (let i = 0; i < 20; i++) {
        const e = tryUnlink(pidFile);
        if (!e || e.code === 'ENOENT') {
            return;
        }
        await sleep(50);
    }
}

async function killOnUnix(pidFile: string, info: PidFileContent, log: (s: string) => void) {
    // Make sure the PID still belongs to our runner and has not been reused by another process.
    // The command line of the runner contains the path of the PID file.
    const res = await run('ps', ['-ww', '-o', 'command=', '-p', String(info.pid)]);
    const cmdLine = res.stdout.trim();
    if (!res.ok || !cmdLine.includes('runYourProgram.py') || !cmdLine.includes(pidFile)) {
        log('PID file was stale, no program to terminate');
        tryUnlink(pidFile);
        return;
    }
    // A shell with job control starts each command in its own process group, so killing
    // the group also kills all processes started by the program. We only kill the group if
    // the runner is its leader, to make sure we never kill the shell itself.
    const target = info.pgid === info.pid ? -info.pid : info.pid;
    const what = target < 0 ? `process group ${info.pid}` : `process ${info.pid}`;
    log(`Terminating ${what}`);
    try {
        process.kill(target, 'SIGTERM');
    } catch (e) {
        log(`Sending SIGTERM to ${what} failed: ${e}`);
    }
    for (let i = 0; i < 20 && isAlive(info.pid); i++) {
        await sleep(50);
    }
    if (isAlive(info.pid)) {
        log(`Process ${info.pid} still alive, sending SIGKILL to ${what}`);
        try {
            process.kill(target, 'SIGKILL');
        } catch (e) {
            log(`Sending SIGKILL to ${what} failed: ${e}`);
        }
    }
    tryUnlink(pidFile);
}

export async function killPreviousRun(pidFile: string, log: (s: string) => void): Promise<void> {
    const info = readPidFile(pidFile);
    if (!info) {
        tryUnlink(pidFile);
        return;
    }
    if (isWindows) {
        await killOnWindows(pidFile, info, log);
    } else {
        await killOnUnix(pidFile, info, log);
    }
}
