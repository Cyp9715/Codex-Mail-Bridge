// Portable stdio launcher. Never downloads runtimes or dependencies.
const { spawn, spawnSync } = require('node:child_process');
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs');

const runtimeRoot = path.join(os.homedir(), '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'python');
const configuredPython = process.env.MAIL_BRIDGE_PYTHON || process.env.THUNDERBIRD_PYTHON;
const candidates = configuredPython
  ? [[configuredPython, []]]
  : [[path.join(runtimeRoot, process.platform === 'win32' ? 'python.exe' : 'bin/python3'), []],
     ...(process.platform === 'win32' ? [['py', ['-3']]] : []),
     ['python3', []], ['python', []]];
let python;
for (const [command, args] of candidates) {
  if (path.isAbsolute(command) && !fs.existsSync(command)) continue;
  const probe = spawnSync(command, [...args, '-c', 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'],
    { stdio: 'ignore', timeout: 5000, windowsHide: true, shell: false });
  if (probe.status === 0) { python = [command, args]; break; }
}
if (!python) {
  process.stderr.write('Mail Bridge requires Python 3.10+. Install it or set MAIL_BRIDGE_PYTHON to its executable.\n');
  process.exit(1);
}
const [command, args] = python;
const child = spawn(command, [...args, '-B', '-u', path.join(__dirname, 'bridge.py'), ...process.argv.slice(2)],
  { stdio: 'inherit', windowsHide: true, shell: false, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
child.on('error', () => { process.stderr.write('Could not start Mail Bridge.\n'); process.exit(1); });
child.on('exit', (code) => process.exit(code ?? 1));
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
