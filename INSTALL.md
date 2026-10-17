# Install and update the Mail Bridge plugin

Use **codex-mail-bridge-0.9.3-plugin.zip** from the GitHub Release.
This is a complete plugin package for the desktop app's **New Plugin** archive
upload. Keep the ZIP intact; no separate installer is required for this workflow.
The source ZIP is for development, not this upload dialog.

## First installation

1. Open Plugins in the desktop app and check whether Mail Bridge already exists
   in the active account or workspace.
2. If it does not exist, open **New Plugin**, choose the **plugin.zip**, and add it.
3. Open Mail Bridge and select **Install plugin** if the host shows that action.
4. Start a new local conversation and select Mail Bridge. Sign in and sync needed
   mail in Thunderbird or classic Outlook first; keep classic Outlook running.
5. Choose the intended mail client and account explicitly. Python 3.10+ and the
   host's command/file permissions are required for the local mail operations.

## Updating an existing plugin

Keep the package name **codex-mail-bridge**. A new version does not require a new
plugin identity. Use the existing plugin's update or upload-new-version action
with the new **plugin.zip**, where the host makes that action available. The
plugin's creator or an authorized workspace editor may need to apply the update.
Reload the plugin or start a new conversation after updating it.

The reported 0.9.1 failure in **New Plugin** was traced by the user to an existing
plugin with the same name. That dialog creates a plugin; it is not an in-place
upgrade. Check for an existing entry before retrying the same archive. Changing
the version or developer credit does not turn creation into an update.

If the host only offers creation, replacement requires deliberately removing the
old entry first. Uninstalling and deleting an account plugin may be different
host actions. Save its package and review sharing before deleting an entry;
replacement can affect its link and collaborators. Prefer the update path.
This package does not delete plugins or change account settings automatically.

The bridge's private mail-account selection settings live outside the plugin.
Do not delete those settings merely to update the plugin package.

## Developer credit

Both manifests set **author.name** and **interface.developerName** to **Cyp**,
and the About description explicitly credits Cyp. The desktop account service
can supply its own developer label for the plugin record. A name shown by that
service is not evidence that a different author string is present in this ZIP.
There is no supported package field here that forces a change to account identity.

A display-name change on the creating account may affect that label, but refresh
behavior for existing plugin records has not been verified. Do not change a shared
account or workspace name solely to change this plugin's credit. Public-directory
submissions separately use the selected verified developer identity; see the
[official submission reference](https://developers.openai.com/plugins/deploy/submission-errors#zip-upload-errors-and-warnings).

## Downloads and verification

| File | Purpose |
| --- | --- |
| `codex-mail-bridge-0.9.3-plugin.zip` | Upload one self-contained Mail Bridge plugin |
| `codex-mail-bridge-0.9.3-source.zip` | Repository source, tests and optional development helpers |
| `SHA256SUMS` | Verify the downloaded release archives |

The plugin ZIP includes its portable manifest, Codex compatibility manifest,
skill, scripts, assets and documentation. The mail operations run locally;
uploading a plugin package does not upload the user's mailbox. Mail and files
retrieved later for an authorized task can reach the AI host.

## Optional repository development

Developers who intentionally use a local marketplace can register the Git source:

```powershell
codex plugin marketplace add Cyp9715/Codex-Mail-Bridge --ref v0.9.3
codex plugin add codex-mail-bridge@cyp-soft-local
```

The source archive retains `install-local.cmd` and `scripts/install-local.cjs`
for that optional workflow. Extract it into a permanent folder before using the
helper. Reuse the same registered folder for later updates; a second folder with
the same marketplace name can conflict. These helpers are not in the plugin ZIP,
and their successful execution does not verify an account-service upload.

See [release validation](docs/RELEASE_VALIDATION.md) for tested behavior and limits.
