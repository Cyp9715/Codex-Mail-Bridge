// Run local publication checks with an existing Python; never install anything.
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs');

const configured = spawnSync('git', ['config', '--local', '--get', 'mailbridge.publicationPython'],
  { encoding: 'utf8', windowsHide: true, shell: false });
const explicit = process.env.MAIL_BRIDGE_PYTHON || (configured.status === 0 ? configured.stdout.trim() : '');
const bundled = path.join(os.homedir(), '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'python',
  process.platform === 'win32' ? 'python.exe' : 'bin/python3');
const candidates = explicit ? [[explicit, []]] : [[bundled, []],
  ...(process.platform === 'win32' ? [['py', ['-3']]] : []), ['python3', []], ['python', []]];
for (const [command, args] of candidates) {
  if (path.isAbsolute(command) && !fs.existsSync(command)) continue;
  const probe = spawnSync(command, [...args, '-c', 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'],
    { stdio: 'ignore', timeout: 5000, windowsHide: true, shell: false });
  if (probe.status !== 0) continue;
  const result = spawnSync(command, [...args, '-B', path.join(__dirname, 'publication_guard.py'), ...process.argv.slice(2)],
    { stdio: 'inherit', windowsHide: true, shell: false, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
  process.exit(result.status ?? 1);
}
process.stderr.write('Publication checks require an existing Python 3.10+; configure MAIL_BRIDGE_PYTHON or mailbridge.publicationPython.\n');
process.exit(1);
