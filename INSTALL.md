# Install Mail Bridge locally

Download **codex-mail-bridge-0.9.2-local.zip** from the GitHub Release and
**extract it completely into a folder you will keep**. On Windows, run
`install-local.cmd` from that folder. It uses an existing Node.js runtime,
including the desktop app's bundled runtime when available.

The installer registers this folder's local marketplace, installs Mail Bridge
through the supported Codex CLI, and checks the installed version and files.
It does not upload the ZIP, read mail, or change script/security policies.
Restart the desktop app and select **Mail Bridge** in a new local conversation.

For a terminal installation on any supported desktop:

```sh
node scripts/install-local.cjs
```

`--check` validates the package and available CLI without installing anything.
If Codex is not on PATH, pass `--codex` with the executable's quoted path.
The Windows helper also checks the desktop app's existing per-user CLI.
Node is only needed by this helper. With the Codex CLI available, the equivalent
manual commands from the extracted folder are:

```sh
codex plugin marketplace add .
codex plugin add codex-mail-bridge@cyp-soft-local
```

Python 3.10+ is required to use the mail tools after installation. Sign in to
Thunderbird or classic Outlook and sync the mail you need. Keep classic Outlook
running. Choose the mail account explicitly in the new conversation.

## Which download to use

| Archive | Purpose |
| --- | --- |
| `*-local.zip` | Recommended desktop installation: installer, marketplace and complete plugin |
| `*-source.zip` | Developer source and tests; includes the same local installer |
| `*-plugin.zip` | One plugin, without a marketplace or installer; for hosts that support plugin package import |

The desktop app's **New Plugin / Upload plugin archive** dialog uploads to the
account service. It is a different operation from local marketplace installation.
A generic "Couldn't add plugin" message does not identify which upload, account,
or package check failed. The local installer avoids that upload path; this release
does not claim to fix the account service or guarantee acceptance there.

Do not upload the local/source ZIP to that dialog: they contain a marketplace
wrapper. Use the local installation steps above. Verify downloads against the
release's `SHA256SUMS`. No OpenAI public-directory approval is implied.

## Updating and troubleshooting

For an existing local installation, extract the new local ZIP into the **same
permanent folder** and run its installer again. Registering the same marketplace
name from another folder is rejected by Codex; the installer preserves that
registration and reports the conflict rather than deleting it automatically.
Keep the source folder registered by `codex plugin marketplace list` available;
the desktop app installs a managed copy and may need the source for later reloads.
Existing private account settings remain outside the plugin package.

If a command fails, the helper prints the failing step and CLI diagnostic, returns
a nonzero exit status, and leaves existing plugins intact. A marketplace may have
been registered before installation failed; correct the reported problem and retry.
Do not delete unrelated marketplaces or bypass an organization's execution policy.

If a previous account upload succeeded, use the existing account plugin's update
action instead of the New Plugin creation dialog. The generic creation error is
not enough evidence to diagnose a duplicate-name conflict.

The [official local-plugin guide](https://developers.openai.com/plugins/build/plugins)
describes marketplace registration and local installation.
