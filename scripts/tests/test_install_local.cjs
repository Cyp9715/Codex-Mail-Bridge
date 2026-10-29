const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const installer = require('../install-local.cjs');

function fixture(t) {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'mail-bridge-install-'));
  t.after(() => fs.rmSync(temporary, { recursive: true, force: true }));
  const root = path.join(temporary, 'source with spaces');
  const plugin = path.join(root, 'plugins/codex-mail-bridge');
  const cache = path.join(temporary, 'installed');
  fs.mkdirSync(path.join(root, '.agents/plugins'), { recursive: true });
  fs.writeFileSync(path.join(root, '.agents/plugins/marketplace.json'), JSON.stringify({
    name: 'cyp-soft-local', plugins: [{ name: 'codex-mail-bridge',
      source: { source: 'local', path: './plugins/codex-mail-bridge' } }]
  }));
  const manifest = { name: 'codex-mail-bridge', version: '0.9.2',
    extensions: { 'com.openai': { requires_local_executor: true } } };
  const files = {
    'plugin.json': JSON.stringify(manifest),
    '.codex-plugin/plugin.json': JSON.stringify({ name: manifest.name, version: manifest.version, requires_local_executor: true }),
    'server/bridge.py': 'VERSION = "0.9.2"',
    'server/accounts.py': '# synthetic account discovery',
    'server/attachments.py': '# synthetic private exports',
    'server/mail_dates.py': '# synthetic dates',
    'server/mail_output.py': '# synthetic bounded output',
    'server/thunderbird_attachments.py': '# synthetic MIME cache',
    'scripts/mail_bridge.cjs': '// synthetic launcher',
    'skills/mail-bridge/SKILL.md': '---\nname: mail-bridge\ndescription: Synthetic test skill.\n---\n'
  };
  for (const [name, data] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(plugin, name)), { recursive: true });
    fs.writeFileSync(path.join(plugin, name), data);
  }
  fs.cpSync(plugin, cache, { recursive: true });
  const calls = [];
  function run(args) {
    calls.push(args);
    if (args.includes('--help')) return 'supported';
    if (args[1] === 'marketplace') return { marketplaceName: 'cyp-soft-local', installedRoot: root };
    return { pluginId: 'codex-mail-bridge@cyp-soft-local', version: '0.9.2', installedPath: cache };
  }
  return { root, plugin, cache, calls, run };
}

test('preflight performs no registration or install', t => {
  const f = fixture(t);
  assert.equal(installer.install(f.root, f.run, true).checkOnly, true);
  assert.equal(f.calls.length, 2);
  assert.ok(f.calls.every(args => args.includes('--help')));
});

test('registers the complete path then verifies installed content', t => {
  const f = fixture(t);
  assert.equal(installer.install(f.root, f.run).version, '0.9.2');
  assert.deepEqual(f.calls[2], ['plugin', 'marketplace', 'add', f.root, '--json']);
  assert.deepEqual(f.calls[3], ['plugin', 'add', 'codex-mail-bridge@cyp-soft-local', '--json']);
});

test('incomplete packages fail before any CLI call', t => {
  const f = fixture(t);
  fs.unlinkSync(path.join(f.plugin, 'skills/mail-bridge/SKILL.md'));
  assert.throws(() => installer.install(f.root, f.run));
  assert.equal(f.calls.length, 0);
});

test('unsupported CLI fails before registration', t => {
  const f = fixture(t);
  assert.throws(() => installer.install(f.root, () => { throw new Error('unsupported CLI'); }), /unsupported CLI/);
});

test('a different marketplace root cannot be reported as success', t => {
  const f = fixture(t);
  assert.throws(() => installer.install(f.root, args => args.includes('--help') ? '' :
    { marketplaceName: 'cyp-soft-local', installedRoot: f.cache }), /different marketplace/);
});

test('a stale installed version cannot be reported as success', t => {
  const f = fixture(t);
  assert.throws(() => installer.install(f.root, args => {
    const result = f.run(args);
    return args[1] === 'add' && !args.includes('--help') ? { ...result, version: '0.9.1' } : result;
  }), /requested plugin version/);
});

test('changed installed skill fails content verification', t => {
  const f = fixture(t);
  fs.writeFileSync(path.join(f.cache, 'skills/mail-bridge/SKILL.md'), 'stale skill');
  assert.throws(() => installer.install(f.root, f.run), /Installed content differs/);
});

test('a retired runtime module cannot remain in an upgraded source', t => {
  const f = fixture(t);
  fs.writeFileSync(path.join(f.plugin, 'server/retired_adapter.py'), '# obsolete adapter');
  assert.throws(() => installer.install(f.root, f.run), /Unexpected runtime files/);
  assert.equal(f.calls.length, 0);
});

test('a retired installed runtime module cannot be reported as a successful update', t => {
  const f = fixture(t);
  fs.writeFileSync(path.join(f.cache, 'server/retired_adapter.py'), '# obsolete adapter');
  assert.throws(() => installer.install(f.root, f.run), /Unexpected runtime files/);
});

test('every installed runtime module must match the requested release', t => {
  const f = fixture(t);
  fs.writeFileSync(path.join(f.cache, 'server/accounts.py'), '# stale account routing');
  assert.throws(() => installer.install(f.root, f.run), /Installed content differs/);
});

test('an explicit missing CLI never falls back to another executable', t => {
  const f = fixture(t);
  assert.throws(() => installer.findCodex(path.join(f.root, 'missing.exe')), /CLI was not found/);
});
