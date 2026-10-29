# Install and update Thunderbird Mail Bridge

Version 0.11.0 retains the package identity `codex-mail-bridge`. It contains one
Thunderbird skill, ten local CLI operations and no MCP server. Python 3.10+ and
local command/file access are required; Node.js is an optional launcher.

## Plugin archive

Use `codex-mail-bridge-0.11.0-plugin.zip` for a host that supports plugin archive
installation or an existing plugin's update action. The source ZIP is for development.
Check whether the plugin already exists before creating another entry. Preserve
the existing plugin identity and sharing; reload or start a new local conversation
after an update. Packaging by itself does not install an account-hosted plugin.

The plugin declares local execution in both manifests. It cannot read a desktop
mailbox from a cloud-only session. The package credits Cyp; an account service can
also display its own account/developer identity.

Before use, sign in and sync needed mail in Thunderbird and allow global indexing
to finish. Select one discovered profile/account explicitly. Its window may then
be closed while existing local index/cache data remains available. The bridge
does not start Thunderbird or sign in.

## Source updates must replace the complete release

Extract each source ZIP into a clean staging folder. Replace the complete
registered source distribution at the same source-root location, including
`scripts/`, `.agents/`, documentation and `plugins/codex-mail-bridge`. Replacing
only the plugin subtree leaves the old installer and its old checks in place.
Replace release-owned directories from the clean extraction rather than overlaying
their contents, so removed files cannot remain. Preserve unrelated development
work separately; Thunderbird profiles and private selection settings are outside
the release and must not be removed.

For a Git checkout, update through Git so tracked file deletions and the new
root-level helper are applied together. Run the helper from the updated source,
then reload the plugin through the supported host workflow.

The optional installer checks the exact six-module Thunderbird runtime and rejects
unexpected or missing runtime files in source or installed copies. It verifies
every runtime module's bytes as well as the manifests, launcher and skill.
An old module left by overlay extraction must be removed by replacing the plugin
directory with the clean package, then retrying the supported install/update flow.
The helper does not delete installed files or edit plugin caches itself.

For intentional local marketplace development, use an existing compatible Codex
CLI with the source helper:

```powershell
node ./scripts/install-local.cjs --check
node ./scripts/install-local.cjs
```

`install-local.cmd` is the Windows wrapper. These source-only helpers register the
complete extracted repository and call the supported plugin installation command.
Use a permanent source location and keep its marketplace identity `cyp-soft-local`.
They do not upload an archive, publish a release or change the user's account choice.

## Files and settings

| File | Purpose |
| --- | --- |
| `codex-mail-bridge-0.11.0-plugin.zip` | One self-contained desktop plugin |
| `codex-mail-bridge-0.11.0-source.zip` | Source, tests and optional installation helpers |

The plugin's `thunderbird.json` selection and private exports live outside the
package. Preserve those settings when updating. A read-only call can reuse an
older Thunderbird selection; it does not migrate settings. Retrieved data and
host-opened originals can reach the AI host under its own policies.

See [validation](docs/RELEASE_VALIDATION.md) and [privacy](docs/privacy.md).
