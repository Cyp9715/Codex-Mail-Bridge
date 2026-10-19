# Privacy notice

Mail Bridge · Cyp · effective October 19, 2026

## Local access

Thunderbird discovery reads registered profiles and limited account/server
preferences; mail queries read its local global search index. Outlook discovery
uses the running classic Windows Outlook profile's account and delivery-store
API. It never guesses or parses PST/OST files. One account per client must be
explicitly selected. Shared Outlook delivery stores are rejected.

Discovery can return profile/account names, addresses, and client metadata to
the AI host. Selected-account queries can return subjects, senders, recipients,
dates, folder names/IDs, message/conversation IDs, body text, and attachment names.
Attachment searches use metadata only. An explicitly requested attachment get
reads one original file and makes it available to the host as a private temporary
local file; images stay as original files for explicit host viewing. The CLI returns no base64 or image pixels. No document parsing
or OCR is performed. The bridge does not read password stores or create, send,
save, delete, move, or mark mail as read.

`outlook_diagnostics` reads only installation/profile-presence and process state;
it returns no paths, profile names or account identities and does not activate COM.
`outlook_start` can explicitly launch the installed classic client with an existing
profile. It does not select a profile or account, log in, force sync or automate
windows. The client may perform its usual startup/synchronization. Other operations
do not start it. Login/profile/security prompts remain the user's responsibility.

## Local storage and network

Private per-client settings hold opaque account/profile IDs and identity
fingerprints outside the plugin. They contain no passwords, addresses, mail,
or absolute profile paths. Read-only calls may read previous-version selections
but never migrate or modify settings. A new explicit selection writes only the
bridge's own settings. Delete current and legacy files to forget selections.

Attachment get creates a generated private local export directory and basename
containing exact original bytes, default 10 MiB and up to 100 MiB when explicitly
allowed through max_bytes. The host receives path, name, size,
hash, content type and export ID. Exports survive command exit so the host can read
them. The default export root is `exports/` under the private settings directory;
`MAIL_BRIDGE_EXPORT_ROOT` can override it locally. Up to 16 files are retained.
Later exports or explicit `--cleanup` remove files older than 10 minutes; a full store
preserves unexpired files and asks the caller to release finished exports.
An OS file lock serializes concurrent export/cleanup operations. `--release <export_id>` removes one finished export.
Cleanup removes only recognized generated files and empty directories, without
recursive deletion or following root/child links. Locked files or no later cleanup
can leave copies. There is no background deletion process. Switching accounts
cannot recall exported files, host copies or chat history.
See [attachment details](ATTACHMENT_SUPPORT.md).

There is no Cyp backend, analytics, telemetry, advertising, payment, or
mail archive. The one-shot local launcher downloads nothing and starts no MCP
server or network listener. The Python/PowerShell bridge
does not directly call a network mail service, but Outlook's configured provider
may fetch data or synchronize as part of its normal client operation. No forced
sync or security-policy change is implemented. Offline operation is not guaranteed.

## AI host and GitHub

Local execution does not make the AI service offline. Retrieved metadata and
mail, requested originals and images are made available to the invoking AI host
under its own settings, storage, and
retention policies. The bridge cannot delete host chat history. Check host
policies and organizational authorization before processing confidential mail.

GitHub hosts this project under its own policies. Voluntary support issues are
public. Do not include private mail or settings. There is no separate support
collection/retention backend.

## Stop access

Disable/uninstall the plugin and delete its current/legacy selection files to
forget account choices. This does not erase Thunderbird/Outlook data or AI-host
history. Use each application's own controls for those records.
See the [README](../README.md) for settings locations and [support](support.md)
for privacy questions, keeping private information out of public issues.
