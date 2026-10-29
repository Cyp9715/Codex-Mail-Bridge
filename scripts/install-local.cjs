// Register and install this extracted distribution through the supported Codex CLI.
// No account upload, mailbox access, direct cache edits, or policy changes.
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const PLUGIN = 'codex-mail-bridge';
const MARKETPLACE = 'cyp-soft-local';
const RUNTIME_FILES = ['accounts.py', 'attachments.py', 'bridge.py', 'mail_dates.py',
                       'mail_output.py', 'thunderbird_attachments.py'];

function verifyRuntimeFiles(pluginRoot) {
  const entries = fs.readdirSync(path.join(pluginRoot, 'server'), { withFileTypes: true })
    .filter(entry => !(entry.name === '__pycache__' && entry.isDirectory()));
  if (entries.some(entry => !entry.isFile()) ||
      JSON.stringify(entries.map(entry => entry.name).sort()) !== JSON.stringify(RUNTIME_FILES)) {
    throw new Error('Unexpected runtime files. Replace the plugin directory with a clean extraction of this release before retrying.');
  }
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
}

function inspectDistribution(root) {
  const catalog = readJson(path.join(root, '.agents/plugins/marketplace.json'));
  const entry = catalog.plugins?.find(item => item.name === PLUGIN);
  if (catalog.name !== MARKETPLACE || entry?.source?.source !== 'local' ||
      entry.source.path !== './plugins/codex-mail-bridge') {
    throw new Error('Extract the complete Mail Bridge source ZIP before this optional CLI installation. The local marketplace is missing or invalid.');
  }
  const pluginRoot = path.join(root, 'plugins', PLUGIN);
  const manifest = readJson(path.join(pluginRoot, 'plugin.json'));
  const overlay = readJson(path.join(pluginRoot, '.codex-plugin/plugin.json'));
  if (manifest.name !== PLUGIN || overlay.name !== PLUGIN ||
      !/^\d+\.\d+\.\d+$/.test(manifest.version) || manifest.version !== overlay.version ||
      manifest.extensions?.['com.openai']?.requires_local_executor !== true ||
      overlay.requires_local_executor !== true) {
    throw new Error('The plugin manifests are inconsistent. Extract a fresh complete source ZIP.');
  }
  for (const name of ['skills/mail-bridge/SKILL.md', 'scripts/mail_bridge.cjs', 'server/bridge.py']) {
    if (!fs.statSync(path.join(pluginRoot, name)).isFile()) throw new Error(`Missing plugin file: ${name}`);
  }
  verifyRuntimeFiles(pluginRoot);
  return { pluginRoot, version: manifest.version };
}

function findCodex(explicit, env = process.env, platform = process.platform) {
  const command = platform === 'win32' ? 'codex.exe' : 'codex';
  const candidates = explicit ? [path.resolve(explicit)] : [
    ...(env.PATH || env.Path || '').split(path.delimiter).filter(Boolean).map(dir => path.join(dir, command)),
    ...(platform === 'win32' && env.LOCALAPPDATA
      ? [path.join(env.LOCALAPPDATA, 'OpenAI', 'Codex', 'bin', command)] : [])
  ];
  const found = candidates.find(file => {
    try { return fs.statSync(file).isFile(); } catch { return false; }
  });
  if (!found) throw new Error('Codex CLI was not found. Open the desktop app once, or pass --codex with the path to the Codex executable.');
  return found;
}

function commandRunner(executable, root) {
  return (args, json = true) => {
    const result = spawnSync(executable, args, {
      cwd: root, encoding: 'utf8', windowsHide: true, shell: false,
      timeout: 120000, maxBuffer: 2 * 1024 * 1024
    });
    if (result.error || result.status !== 0) {
      const reason = result.error?.message || result.stderr?.trim() || result.stdout?.trim() || `exit ${result.status}`;
      throw new Error(`Codex ${args.slice(0, 3).join(' ')} failed: ${reason}`);
    }
    if (!json) return result.stdout.trim();
    try { return JSON.parse(result.stdout); }
    catch { throw new Error('Codex returned an invalid install response. Update the Codex CLI and retry.'); }
  };
}

function canonical(file) {
  return fs.realpathSync.native(file).replace(/^\\\\\?\\/, '').replace(/[\\/]+$/, '');
}

function install(root, run, checkOnly = false) {
  const expected = inspectDistribution(root);
  // Fail before writing configuration when the installed CLI lacks this workflow.
  run(['plugin', 'marketplace', 'add', '--help'], false);
  run(['plugin', 'add', '--help'], false);
  if (checkOnly) return { ok: true, checkOnly: true, version: expected.version };

  const registered = run(['plugin', 'marketplace', 'add', root, '--json']);
  if (registered.marketplaceName !== MARKETPLACE || !registered.installedRoot ||
      canonical(registered.installedRoot) !== canonical(root)) {
    throw new Error('Codex registered a different marketplace source. Inspect `codex plugin marketplace list` before retrying.');
  }
  const installed = run(['plugin', 'add', `${PLUGIN}@${MARKETPLACE}`, '--json']);
  if (installed.pluginId !== `${PLUGIN}@${MARKETPLACE}` || installed.version !== expected.version ||
      !installed.installedPath || !path.isAbsolute(installed.installedPath)) {
    throw new Error('Codex did not confirm the requested plugin version. The marketplace may be registered; inspect it before retrying.');
  }
  verifyRuntimeFiles(installed.installedPath);
  // Verify all runtime modules as well as the installed skill and manifests.
  for (const name of ['plugin.json', '.codex-plugin/plugin.json', 'skills/mail-bridge/SKILL.md',
                      'scripts/mail_bridge.cjs', ...RUNTIME_FILES.map(name => `server/${name}`)]) {
    if (!fs.readFileSync(path.join(expected.pluginRoot, name)).equals(fs.readFileSync(path.join(installed.installedPath, name)))) {
      throw new Error(`Installed content differs from this release: ${name}`);
    }
  }
  return { ok: true, version: expected.version, pluginId: installed.pluginId, installedPath: installed.installedPath };
}

function main(argv = process.argv.slice(2)) {
  let checkOnly = false, executable = process.env.MAIL_BRIDGE_CODEX;
  for (let index = 0; index < argv.length; index++) {
    if (argv[index] === '--help') {
      console.log('Usage: node scripts/install-local.cjs [--check] [--codex EXECUTABLE]\nOptional developer workflow: extract the source ZIP into a folder you will keep. This registers its local marketplace and installs Mail Bridge.\nFor desktop New Plugin uploads, use the plugin ZIP instead.\n--check validates the distribution and CLI without changing configuration.');
      return;
    }
    if (argv[index] === '--check') checkOnly = true;
    else if (argv[index] === '--codex' && argv[index + 1]) executable = argv[++index];
    else throw new Error(`Unknown or incomplete option: ${argv[index]}`);
  }
  const root = path.resolve(__dirname, '..');
  const result = install(root, commandRunner(findCodex(executable), root), checkOnly);
  console.log(JSON.stringify(result, null, 2));
  if (!checkOnly) console.error('Mail Bridge is installed. Keep this extracted folder for future reloads. Restart the desktop app and select Mail Bridge in a new local conversation.');
}

module.exports = { inspectDistribution, findCodex, commandRunner, install, main };
if (require.main === module) {
  try { main(); }
  catch (error) { console.error(`Mail Bridge installation failed: ${error.message}`); process.exitCode = 1; }
}
