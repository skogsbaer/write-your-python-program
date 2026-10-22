import * as assert from 'assert';
import { ChildProcess, spawn } from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

import { killPreviousRun } from '../../killPreviousRun';

const repoRoot = path.join(__dirname, '..', '..', '..');
const runProg = path.join(repoRoot, 'python', 'code', 'wypp', 'runYourProgram.py');

function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function isAlive(pid: number): boolean {
    try {
        process.kill(pid, 0);
        return true;
    } catch (e) {
        return false;
    }
}

async function waitFor(cond: () => boolean, what: string, timeoutMs = 10000) {
    const end = Date.now() + timeoutMs;
    while (!cond()) {
        if (Date.now() > end) {
            throw new Error(`Timeout waiting for ${what}`);
        }
        await sleep(50);
    }
}

function exited(proc: ChildProcess): Promise<void> {
    return new Promise((resolve) => {
        if (proc.exitCode !== null || proc.signalCode !== null) {
            resolve();
        } else {
            proc.on('exit', () => resolve());
        }
    });
}

suite('killPreviousRun', function () {
    // The tests start python processes; killing processes works differently on Windows.
    if (process.platform === 'win32') {
        return;
    }
    this.timeout(20000);

    let dir: string;
    let pidFile: string;
    const procs: ChildProcess[] = [];
    const log = (_s: string) => {};

    setup(() => {
        dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wypp-kill-test-'));
        pidFile = path.join(dir, 'wypp.pid');
    });

    teardown(() => {
        for (const p of procs) {
            try { process.kill(-p.pid!, 'SIGKILL'); } catch (e) { /* already dead */ }
        }
        procs.length = 0;
        fs.rmSync(dir, { recursive: true, force: true });
    });

    // Starts the runner like the RUN button does. detached: the runner gets its own
    // process group, as it does when started by a shell with job control.
    // The student program starts a child process and then runs forever.
    async function startRunner(extraCode = ''): Promise<{ runner: ChildProcess, childPid: number }> {
        const childPidFile = path.join(dir, 'child.pid');
        const prog = path.join(dir, 'prog.py');
        fs.writeFileSync(prog, [
            'import subprocess, time',
            extraCode,
            `p = subprocess.Popen(['sleep', '60'])`,
            `open(${JSON.stringify(childPidFile)}, 'w').write(str(p.pid))`,
            'while True:',
            '    time.sleep(0.1)',
            ''
        ].join('\n'));
        const runner = spawn('python3',
            [runProg, '--quiet', '--no-clear', '--interactive', '--pid-file', pidFile, prog],
            { detached: true, stdio: 'ignore' });
        procs.push(runner);
        await waitFor(() => fs.existsSync(childPidFile) && fs.readFileSync(childPidFile, 'utf-8') !== '',
                      'child process to start');
        const childPid = parseInt(fs.readFileSync(childPidFile, 'utf-8'));
        return { runner, childPid };
    }

    test('does nothing if there is no PID file', async () => {
        await killPreviousRun(pidFile, log);
        assert.ok(!fs.existsSync(pidFile));
    });

    test('kills the runner and the processes it started', async () => {
        const { runner, childPid } = await startRunner();
        assert.ok(fs.existsSync(pidFile));
        assert.ok(isAlive(childPid));
        await killPreviousRun(pidFile, log);
        await exited(runner);
        await waitFor(() => !isAlive(childPid), 'child process to terminate');
        assert.ok(!fs.existsSync(pidFile));
    });

    test('uses SIGKILL if the runner ignores SIGTERM', async () => {
        const { runner, childPid } = await startRunner(
            'import signal; signal.signal(signal.SIGTERM, signal.SIG_IGN)');
        await killPreviousRun(pidFile, log);
        await exited(runner);
        assert.strictEqual(runner.signalCode, 'SIGKILL');
        await waitFor(() => !isAlive(childPid), 'child process to terminate');
    });

    test('removes a PID file of a process that has already exited', async () => {
        const { runner } = await startRunner();
        const content = fs.readFileSync(pidFile, 'utf-8');
        process.kill(-runner.pid!, 'SIGKILL');
        await exited(runner);
        fs.writeFileSync(pidFile, content); // SIGKILL leaves the PID file behind
        await killPreviousRun(pidFile, log);
        assert.ok(!fs.existsSync(pidFile));
    });

    test('does not kill a process that is not the runner', async () => {
        // e.g. the PID has been reused by another process
        const other = spawn('sleep', ['60'], { detached: true, stdio: 'ignore' });
        procs.push(other);
        fs.writeFileSync(pidFile, JSON.stringify({ pid: other.pid, pgid: other.pid }));
        await killPreviousRun(pidFile, log);
        await sleep(200);
        assert.ok(isAlive(other.pid!));
        assert.ok(!fs.existsSync(pidFile));
    });

    test('ignores a garbled PID file', async () => {
        fs.writeFileSync(pidFile, 'garbage');
        await killPreviousRun(pidFile, log);
        assert.ok(!fs.existsSync(pidFile));
    });
});
